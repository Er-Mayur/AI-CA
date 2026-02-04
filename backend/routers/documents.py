from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models import User, Document, ActivityHistory, DocType, VerificationStatus
from schemas import DocumentResponse
from dependencies import get_current_user
from typing import List
import os
import shutil
from datetime import datetime
from utils.pdf_processor import verify_document, extract_document_data
from utils.rag_engine import RAGEngine

rag = RAGEngine()

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    financial_year: str = Form(...),
    doc_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Convert doc_type string to enum
    try:
        doc_type_enum = DocType(doc_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {', '.join([e.value for e in DocType])}"
        )
    
    # Check if document already exists
    existing_doc = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.financial_year == financial_year,
        Document.doc_type == doc_type_enum
    ).first()
    
    # If exists, mark as replacement (we'll handle this in frontend confirmation)
    # For now, we'll delete the old one
    if existing_doc:
        # Delete old file
        if os.path.exists(existing_doc.file_path):
            os.remove(existing_doc.file_path)
        db.delete(existing_doc)
        db.commit()
    
    # IMPORTANT: Save file to temporary location FIRST for verification
    import tempfile
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"temp_{current_user.id}_{datetime.now().timestamp()}.pdf")
    
    # Save uploaded file to temporary location
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # CRITICAL: Verify document BEFORE saving to permanent location
    try:
        verification_result = await verify_document(
            temp_file_path, 
            current_user.name, 
            current_user.pan_card, 
            doc_type_enum,
            financial_year  # Pass the expected financial year for verification
        )
        
        # If verification fails, delete temp file and return error
        if not verification_result["verified"]:
            # Delete temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            # Log failed verification attempt
            activity = ActivityHistory(
                user_id=current_user.id,
                financial_year=financial_year,
                activity_type="DOCUMENT_VERIFICATION_FAILED",
                description=f"Document {doc_type_enum.value} verification failed: {verification_result.get('message', 'Verification failed')}",
                activity_metadata={"error_type": verification_result.get('error_type'), "filename": file.filename}
            )
            db.add(activity)
            db.commit()
            
            # Return HTTP error with detailed message
            error_message = verification_result.get('message', 'Document verification failed')
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message  # Return full message for detailed display
            )
        
        # VERIFICATION PASSED - Now save to permanent location
        user_dir = os.path.join(UPLOAD_DIR, str(current_user.id), financial_year)
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, f"{doc_type_enum.value}_{datetime.now().timestamp()}.pdf")
        
        # Copy from temp to permanent location
        shutil.copy2(temp_file_path, file_path)
        
        # Delete temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # REUSE Verification Data instead of extracting again
        # The verify_document function already extracts data (via smart pattern matching)
        # We can use that as a starting point and only augment with AI if needed
        initial_extracted_data = verification_result.get("extracted_data", {})
        extracted_text_content = verification_result.get("text_content")
        
        # Create document record
        document = Document(
            user_id=current_user.id,
            financial_year=financial_year,
            doc_type=doc_type_enum,
            file_path=file_path,
            verification_status=VerificationStatus.VERIFIED,
            verification_message=verification_result.get("message", "Document verified successfully"),
            verified_at=datetime.utcnow(),
            extracted_data=initial_extracted_data # Save initial extraction immediately
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Log successful upload
        activity = ActivityHistory(
            user_id=current_user.id,
            financial_year=financial_year,
            activity_type="DOCUMENT_UPLOAD",
            description=f"Uploaded and verified {doc_type_enum.value} for FY {financial_year}",
            activity_metadata={"document_id": document.id, "filename": file.filename}
        )
        db.add(activity)
        db.commit()
        
        # OPTIMIZATION: Only run full AI extraction if critical data is missing from verification
        # Verification phase already extracts PAN, FY, Name via regex
        # If we have those, we might not need full AI extraction right away
        
        has_critical_data = (
            initial_extracted_data.get('pan') and 
            initial_extracted_data.get('financial_year') and
            initial_extracted_data.get('gross_salary') # Smart extractor tries to find this too
        )
        
        # Only run deep extraction if we are missing data OR if it's a scanned PDF (where smart extraction is limited)
        # Check if it was a scanned PDF by looking at confidence or extracted fields
        try:
            final_extracted_data = document.extracted_data or {}
            
            # If verification returned high confidence data, just use it!
            if has_critical_data:
                 print(f"Skipping redundant AI extraction - verification already provided data")
            else:
                 # Only perform AI extraction if current data is insufficient
                 print(f"Performing deep data extraction for missing fields...")
                 # Pass the already extracted text to avoid re-running OCR
                 extracted_data = await extract_document_data(
                     file_path, 
                     doc_type_enum, 
                     financial_year,
                     text_content=extracted_text_content
                 )
                 
                 # Merge with initial data (prefer AI data for specific fields, pattern data for IDs)
                 # Update ONLY missing fields to avoid overwriting good data
                 current_data = document.extracted_data or {}
                 current_data.update(extracted_data)
                 document.extracted_data = current_data
                 db.commit()
                 
                 final_extracted_data = current_data
            
            # === RAG INTEGRATION START ===
            # Trigger Indexing immediately after data is finalized
            print(f"🧠 RAG: Indexing {doc_type_enum.value} for FY {financial_year}...")
            
            rag.index_user_document(
                user_id=current_user.id,
                doc_type=doc_type_enum.value,
                financial_year=financial_year,
                data=final_extracted_data
            )
            print(f"✅ RAG: Indexing complete.")
            # === RAG INTEGRATION END ===
            
            # Log data extraction
            activity = ActivityHistory(
                user_id=current_user.id,
                financial_year=financial_year,
                activity_type="DOCUMENT_VERIFIED",
                description=f"Document {doc_type_enum.value} verified and indexed for AI",
                activity_metadata={"document_id": document.id}
            )
            db.add(activity)
            db.commit()
            db.refresh(document)
        except Exception as e:
            # Data extraction failed, but document is verified
            print(f"[WARNING] Data extraction/Indexing failed: {str(e)}")
            # Don't fail the upload, just log the warning
        
        return document
        
    except HTTPException:
        # Re-raise HTTP exceptions (verification failures)
        raise
    except Exception as e:
        # Delete temporary file on any error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Log error
        activity = ActivityHistory(
            user_id=current_user.id,
            financial_year=financial_year,
            activity_type="DOCUMENT_UPLOAD_ERROR",
            description=f"Error during document upload: {str(e)}",
            activity_metadata={"filename": file.filename}
        )
        db.add(activity)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/list/{financial_year}", response_model=List[DocumentResponse])
def list_documents(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.financial_year == financial_year
    ).order_by(Document.uploaded_at.desc()).all()
    
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Log activity
    activity = ActivityHistory(
        user_id=current_user.id,
        financial_year=document.financial_year,
        activity_type="DOCUMENT_DELETED",
        description=f"Deleted {document.doc_type.value} for FY {document.financial_year}"
    )
    db.add(activity)
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

