from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import User, Document, ActivityHistory, DocType, VerificationStatus, ProcessingStatus
from schemas import DocumentResponse, DocumentStatusResponse
from dependencies import get_current_user
from typing import List
import os
import shutil
from datetime import datetime
from utils.pdf_processor import verify_document, extract_document_data
from utils.rag_engine import get_rag_engine

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def verify_and_extract_task(document_id: int, db: Session):
    """
    Background task to verify, extract, and index a document.
    """
    # Get the document from the database
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        print(f"[BG_TASK] Document with ID {document_id} not found. Aborting.")
        return

    # Get user associated with the document
    current_user = db.query(User).filter(User.id == document.user_id).first()
    if not current_user:
        document.processing_status = ProcessingStatus.FAILED
        document.verification_message = "User not found."
        db.commit()
        return

    # Update status to PROCESSING
    document.processing_status = ProcessingStatus.PROCESSING
    db.commit()

    try:
        # CRITICAL: Verify document
        verification_result = await verify_document(
            document.file_path,
            current_user.name,
            current_user.pan_card,
            document.doc_type,
            document.financial_year
        )

        if not verification_result["verified"]:
            document.processing_status = ProcessingStatus.FAILED
            document.verification_status = VerificationStatus.FAILED
            document.verification_message = verification_result.get('message', 'Verification failed')
            db.commit()
            # Log failed verification attempt
            activity = ActivityHistory(
                user_id=current_user.id,
                financial_year=document.financial_year,
                activity_type="DOCUMENT_VERIFICATION_FAILED",
                description=f"Document {document.doc_type.value} verification failed: {verification_result.get('message', 'Verification failed')}",
                activity_metadata={"error_type": verification_result.get('error_type'), "filename": os.path.basename(document.file_path)}
            )
            db.add(activity)
            db.commit()
            return

        # VERIFICATION PASSED
        document.verification_status = VerificationStatus.VERIFIED
        document.verification_message = verification_result.get("message", "Document verified successfully")
        document.verified_at = datetime.utcnow()
        document.extracted_data = verification_result.get("extracted_data", {})
        db.commit()

        # Perform comprehensive data extraction
        extracted_text_content = verification_result.get("text_content")
        extracted_data = await extract_document_data(
            document.file_path,
            document.doc_type,
            document.financial_year,
            text_content=extracted_text_content
        )

        # Merge with initial data
        current_data = document.extracted_data or {}
        current_data.update(extracted_data)
        document.extracted_data = current_data
        db.commit()

        # RAG Indexing
        rag = get_rag_engine()
        rag.index_user_document(
            user_id=current_user.id,
            doc_type=document.doc_type.value,
            financial_year=document.financial_year,
            data=document.extracted_data
        )

        # All done, mark as SUCCESS
        document.processing_status = ProcessingStatus.SUCCESS
        db.commit()

        # Log success
        activity = ActivityHistory(
            user_id=current_user.id,
            financial_year=document.financial_year,
            activity_type="DOCUMENT_PROCESSED",
            description=f"Successfully processed and indexed {document.doc_type.value} for FY {document.financial_year}",
            activity_metadata={"document_id": document.id}
        )
        db.add(activity)
        db.commit()

    except Exception as e:
        document.processing_status = ProcessingStatus.FAILED
        document.verification_message = f"An unexpected error occurred: {str(e)}"
        db.commit()
        # Log error
        activity = ActivityHistory(
            user_id=current_user.id,
            financial_year=document.financial_year,
            activity_type="DOCUMENT_PROCESSING_ERROR",
            description=f"Error during document processing: {str(e)}",
            activity_metadata={"document_id": document.id}
        )
        db.add(activity)
        db.commit()
        print(f"[BG_TASK] Error processing document {document_id}: {e}")


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
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

    # Save file to a permanent location immediately
    user_dir = os.path.join(UPLOAD_DIR, str(current_user.id), financial_year)
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, f"{doc_type_enum.value}_{datetime.now().timestamp()}.pdf")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create document record with PENDING status
    document = Document(
        user_id=current_user.id,
        financial_year=financial_year,
        doc_type=doc_type_enum,
        file_path=file_path,
        processing_status=ProcessingStatus.PENDING,
        verification_status=VerificationStatus.PENDING
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Add the verification and extraction task to the background
    background_tasks.add_task(verify_and_extract_task, document.id, db)

    # Log upload attempt
    activity = ActivityHistory(
        user_id=current_user.id,
        financial_year=financial_year,
        activity_type="DOCUMENT_UPLOAD_QUEUED",
        description=f"Queued {doc_type_enum.value} for FY {financial_year} for processing.",
        activity_metadata={"document_id": document.id, "filename": file.filename}
    )
    db.add(activity)
    db.commit()

    return document


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

@router.get("/status/{document_id}", response_model=DocumentStatusResponse)
def get_document_status(
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

