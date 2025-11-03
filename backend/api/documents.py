# backend/api/documents.py
import os
import json
import shutil
import re
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.database import get_db
from db.models import Document, DocumentHistory
from core.security import get_current_user
from services.llm_client import extract_text_from_pdf
from services.parser import verify_document  # Fuzzy verification logic

router = APIRouter(prefix="/documents", tags=["Documents"])


# --------------------------------------------------------------------
# Helper: Standardize safe filenames
# --------------------------------------------------------------------
def slugify_name(value: str) -> str:
    """Convert string to lowercase, underscore-separated filename-safe value."""
    return re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")


# --------------------------------------------------------------------
# 1️⃣ Upload / Replace Document
# --------------------------------------------------------------------
@router.post("/upload")
async def upload_document(
    fy: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    replace: bool = Form(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload, replace, and verify Form 16 / 26AS / AIS.
    SAFE + USER-FRIENDLY:
    - Blocks duplicate uploads unless replace=true
    - Verifies using staged temp file
    - Promotes to final only on success
    """
    allowed_types = {"form 16", "form 26as", "ais"}
    if doc_type.lower() not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid document type")

    # --------------------------------------------------------------------
    # 1️⃣ Setup upload directory + standardized base names
    # --------------------------------------------------------------------
    upload_dir = os.path.join("uploads", str(current_user.id), fy)
    os.makedirs(upload_dir, exist_ok=True)

    safe_username = re.sub(r"[^a-zA-Z0-9]+", "_", current_user.name.lower()).strip("_")
    safe_doc_type = re.sub(r"[^a-zA-Z0-9]+", "_", doc_type.lower()).strip("_")
    base_filename = f"{safe_username}_{safe_doc_type}"
    final_pdf_filename = f"{base_filename}.pdf"
    final_ocr_filename = f"{base_filename}_ocr_text.txt"

    final_pdf_path = os.path.join(upload_dir, final_pdf_filename)
    final_ocr_path = os.path.join(upload_dir, final_ocr_filename)

    # Staged temp names (unique)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    tmp_tag = f"{uuid.uuid4().hex[:8]}_{stamp}"
    staged_pdf_path = os.path.join(upload_dir, f"{base_filename}__incoming__{tmp_tag}.pdf")
    staged_ocr_path = os.path.splitext(staged_pdf_path)[0] + "_ocr_text.txt"

    # --------------------------------------------------------------------
    # 2️⃣ Check if document already exists for this user + FY + type
    # --------------------------------------------------------------------
    existing_doc = (
    db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.fy == fy,
        func.lower(Document.doc_type) == doc_type.lower(),
        ).first()
    )

    if existing_doc and not replace:
        # 🔒 Stop here if not replacing
        return {
            "exists": True,
            "verified": False,
            "message": f"{doc_type.upper()} for FY {fy} already exists. Use replace=true to update it.",
            "file_path": existing_doc.file_path,
        }

    # --------------------------------------------------------------------
    # 3️⃣ Save to STAGED path (safe temp)
    # --------------------------------------------------------------------
    try:
        file.file.seek(0)
        with open(staged_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        size = os.path.getsize(staged_pdf_path)
        print(f"📄 PDF staged → {staged_pdf_path} ({size} bytes)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded PDF: {e}")

    # --------------------------------------------------------------------
    # 4️⃣ OCR + Extraction
    # --------------------------------------------------------------------
    extracted_text = extract_text_from_pdf(staged_pdf_path)
    if not extracted_text or len(extracted_text.strip()) < 50:
        try:
            if os.path.exists(staged_pdf_path): os.remove(staged_pdf_path)
            if os.path.exists(staged_ocr_path): os.remove(staged_ocr_path)
        finally:
            pass
        raise HTTPException(status_code=400, detail="Failed to extract readable text from PDF.")

    print(f"🧾 OCR (staged) → {staged_ocr_path} (exists={os.path.exists(staged_ocr_path)})")

    # --------------------------------------------------------------------
    # 5️⃣ Verification Logic (uses parser.py)
    # --------------------------------------------------------------------
    verification = verify_document(staged_pdf_path, doc_type, current_user, fy)
    verified = verification["verified"]
    confidence = verification["confidence"]
    issues = verification["issues"]
    metadata = verification["metadata"]

    print(f"🧠 Verification Summary: {verification}")

    # --------------------------------------------------------------------
    # 6️⃣ If verification failed → clean staged files, keep old intact
    # --------------------------------------------------------------------
    if not verified:
        for p in [staged_pdf_path, staged_ocr_path]:
            if os.path.exists(p):
                os.remove(p)
        return {
            "verified": False,
            "confidence": confidence,
            "issues": issues,
            "metadata": metadata,
            "message": "Verification failed. Please upload the correct document."
        }

    # --------------------------------------------------------------------
    # 7️⃣ Verified → Move staged to final; handle replace safely
    # --------------------------------------------------------------------
    try:
        os.makedirs(upload_dir, exist_ok=True)

        # Remove old verified files if replacing
        if replace and os.path.exists(final_pdf_path):
            os.remove(final_pdf_path)
        if replace and os.path.exists(final_ocr_path):
            os.remove(final_ocr_path)

        # Promote staged → final
        os.replace(staged_pdf_path, final_pdf_path)
        if os.path.exists(staged_ocr_path):
            os.replace(staged_ocr_path, final_ocr_path)

        print(f"✅ Promoted → {final_pdf_path}")
        if os.path.exists(final_ocr_path):
            print(f"✅ OCR Finalized → {final_ocr_path}")
    except Exception as e:
        for p in [staged_pdf_path, staged_ocr_path]:
            if os.path.exists(p):
                os.remove(p)
        raise HTTPException(status_code=500, detail=f"Failed to promote verified files: {e}")

    # --------------------------------------------------------------------
    # 8️⃣ Update DB entries
    # --------------------------------------------------------------------
    if existing_doc and replace:
        old_path = existing_doc.file_path
        db.delete(existing_doc)
        db.commit()

        db.add(
            DocumentHistory(
                user_id=current_user.id,
                fy=fy,
                doc_type=doc_type.lower(),
                old_file_path=old_path,
                new_file_path=final_pdf_path,
                action="replaced",
                timestamp=datetime.utcnow(),
            )
        )

    new_doc = Document(
        user_id=current_user.id,
        fy=fy,
        doc_type=metadata.get("detected_type", doc_type.lower()),
        file_path=final_pdf_path,
        uploaded_at=datetime.utcnow(),
        is_verified=True,
        parsed_json=json.dumps(metadata),
        verification_json=json.dumps(verification),
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    db.add(
        DocumentHistory(
            user_id=current_user.id,
            fy=fy,
            doc_type=doc_type.lower(),
            new_file_path=final_pdf_path,
            action="uploaded" if not replace else "replaced",
            timestamp=datetime.utcnow(),
        )
    )
    db.commit()

    # --------------------------------------------------------------------
    # 9️⃣ Response
    # --------------------------------------------------------------------
    return {
        "verified": True,
        "confidence": confidence,
        "metadata": metadata,
        "issues": issues,
        "message": f"{doc_type.upper()} {'replaced' if replace else 'uploaded'} and verified successfully for FY {fy}",
        "file_path": final_pdf_path,
        "ocr_text_path": final_ocr_path if os.path.exists(final_ocr_path) else None,
        "fy": fy,
        "name_similarity": verification.get("name_similarity"),
        "replaced": replace,
    }

# --------------------------------------------------------------------
# 2️⃣ List Documents by FY
# --------------------------------------------------------------------
@router.get("/list")
def list_documents(
    fy: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all uploaded & verified documents for a given FY."""
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id, Document.fy == fy)
        .all()
    )

    return [
        {
            "id": d.id,
            "doc_type": d.doc_type,
            "file_path": d.file_path,
            "is_verified": d.is_verified,
            "confidence": json.loads(d.verification_json or "{}").get("confidence"),
            "uploaded_at": d.uploaded_at,
        }
        for d in docs
    ]


# --------------------------------------------------------------------
# 3️⃣ Delete a Document (with History)
# --------------------------------------------------------------------
@router.delete("/delete/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a document and log history."""
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.user_id == current_user.id)
        .first()
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.add(
        DocumentHistory(
            user_id=current_user.id,
            fy=doc.fy,
            doc_type=doc.doc_type,
            old_file_path=doc.file_path,
            action="deleted",
            timestamp=datetime.utcnow(),
        )
    )
    db.delete(doc)
    db.commit()

    return {"message": f"{doc.doc_type.upper()} for FY {doc.fy} deleted successfully"}
