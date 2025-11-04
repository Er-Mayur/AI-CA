# backend/api/summary.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from db.database import get_db
from db.models import Document, TaxSummary, Deduction
from core.security import get_current_user
from services.structured_extractor import extract_structured
from services.reconcile import reconcile_priority
from core.tax_engine import compute_tax

router = APIRouter(prefix="/summary", tags=["Summary"])

@router.post("/parse/{doc_id}")
def parse_document(doc_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id==doc_id, Document.user_id==current_user.id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    # 1) load OCR (or re-extract)
    with open(doc.file_path.replace(".pdf", "_ocr_text.txt"), "r", encoding="utf-8") as f:
        raw = f.read()
    structured, cleaned = extract_structured(raw)

    # stash structured JSON into documents.parsed_json for trace
    doc.parsed_json = structured.model_dump_json()
    db.commit()

    return {"ok": True, "structured": structured.model_dump(), "cleaned_len": len(cleaned)}

@router.get("/dashboard")
def dashboard(fy: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Fuse all docs for FY, compute tax, return ready-to-render payload."""
    docs = (
        db.query(Document)
        .filter(Document.user_id==current_user.id, Document.fy==fy)
        .all()
    )
    if not docs:
        return {"docs": [], "summary": None}

    # collect structured
    from schemas.tax_schemas import StructuredTaxDoc
    combined = None
    for d in docs:
        if not d.parsed_json or d.parsed_json == "{}":
            # fallback quick-parse from OCR if not parsed yet
            try:
                with open(d.file_path.replace(".pdf", "_ocr_text.txt"), "r", encoding="utf-8") as f:
                    raw = f.read()
                st, _ = extract_structured(raw)
            except Exception:
                continue
        else:
            st = StructuredTaxDoc.model_validate_json(d.parsed_json)

        if combined is None:
            combined = st
        else:
            # heuristics: if this one is Form 16, use it as base
            if (st.identity.doc_type or "").lower().strip() == "form 16":
                combined = reconcile_priority(st, combined)
            else:
                combined = reconcile_priority(combined, st)

    if not combined:
        return {"docs": [], "summary": None}

    summary = compute_tax(combined)
    return {
        "docs": [{"id": d.id, "type": d.doc_type, "verified": d.is_verified} for d in docs],
        "identity": combined.identity.model_dump(),
        "numbers": summary,
    }
