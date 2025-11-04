# backend/services/llm_client.py
# -------------------------------------------------------------
# 🔹 Hybrid Document Intelligence Engine
# Robust to OCR noise, A4F API failures, and layout variations
# -------------------------------------------------------------
import os
import re
import pytesseract
import torch
from typing import Dict
from pdf2image import convert_from_path
from transformers import pipeline
from fuzzywuzzy import fuzz
from core.config import TESSERACT_PATH, POPPLER_PATH
from services.semantic_extractor import extract_metadata_from_pdf_path

# --------------------------------------------------------------------
# 1️⃣ Hardware setup & macOS paths
# --------------------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
DEVICE = 0 if torch.backends.mps.is_available() else -1
print(f"🚀 Using device: {'Apple MPS GPU' if DEVICE == 0 else 'CPU'}")

CLASSIFIER = None
NER = None


# --------------------------------------------------------------------
# 2️⃣ Lazy pipeline loader
# --------------------------------------------------------------------
def _ensure_pipelines() -> None:
    """
    Load Hugging Face pipelines (only once).
    Used for fallback doc classification & entity detection.
    """
    global CLASSIFIER, NER
    if CLASSIFIER and NER:
        return
    try:
        print("⏳ Loading Hugging Face pipelines ...")
        CLASSIFIER = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=DEVICE,
        )
        NER = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple",
            device=DEVICE,
        )
        print("✅ Pipelines ready.")
    except Exception as e:
        print(f"⚠️ Pipeline init failed: {e}")
        CLASSIFIER, NER = None, None


# --------------------------------------------------------------------
# 3️⃣ PDF text extractors (pdfminer + OCR fallback)
# --------------------------------------------------------------------
def _extract_text_pdfminer(pdf_path: str) -> str:
    """Vector text extraction (fast + clean)."""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(pdf_path) or ""
        return text.replace("\x00", "")
    except Exception as e:
        print(f"⚠️ pdfminer failed: {e}")
        return ""


def _extract_text_ocr(pdf_path: str, dpi: int = 300) -> str:
    """OCR fallback for scanned/image PDFs."""
    try:
        pages = convert_from_path(
            pdf_path, dpi=dpi, first_page=1, last_page=5, poppler_path=POPPLER_PATH
        )
        text = "\n".join(pytesseract.image_to_string(p) for p in pages)
        return text
    except Exception as e:
        print(f"⚠️ OCR fallback failed: {e}")
        return ""


# --------------------------------------------------------------------
# 4️⃣ Unified text extraction
# --------------------------------------------------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using pdfminer first; fallback to OCR if needed.
    Always saves text snapshot for debugging.
    """
    text = _extract_text_pdfminer(pdf_path)
    if not text or len(text.strip()) < 100:
        text = _extract_text_ocr(pdf_path)

    text = text.replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]
    text = "\n".join(lines)

    try:
        dir_name = os.path.dirname(pdf_path)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        ocr_name = f"{base}_ocr_text.txt"
        ocr_path = os.path.join(dir_name, ocr_name)
        with open(ocr_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"🧾 OCR text saved → {ocr_path} ({len(text)} chars)")
    except Exception as e:
        print(f"⚠️ Debug save failed: {e}")

    return text


# --------------------------------------------------------------------
# 5️⃣ Document classifier (fallback when LLM fails)
# --------------------------------------------------------------------
def classify_document_type(text: str) -> Dict[str, str]:
    """
    Optional zero-shot classifier for document type.
    Runs only if A4F model returns 'unknown' or fails.
    """
    _ensure_pipelines()
    if not CLASSIFIER:
        return {"type": "unknown", "confidence": 0.0}

    try:
        labels = ["Form 16", "Form 26AS", "AIS", "TDS Certificate", "Payslip"]
        result = CLASSIFIER(text[:1500], candidate_labels=labels)
        label = result["labels"][0]
        conf = float(result["scores"][0])
        return {"type": label.lower(), "confidence": round(conf, 2)}
    except Exception as e:
        print(f"⚠️ Classification failed: {e}")
        return {"type": "unknown", "confidence": 0.0}


# --------------------------------------------------------------------
# 6️⃣ Main hybrid extractor
# --------------------------------------------------------------------
def classify_and_extract_metadata(pdf_path: str) -> dict:
    """
    Hybrid metadata extractor pipeline:
      1. Extract text (pdfminer → OCR)
      2. Use semantic_extractor (A4F + local fallback)
      3. If doc type unknown → zero-shot classifier
      4. Returns final structured metadata dict
    """
    try:
        # Step 1: OCR / text save
        _ = extract_text_from_pdf(pdf_path)

        # Step 2: Semantic layout extraction
        metadata = extract_metadata_from_pdf_path(pdf_path)

        # Step 3: Classifier enrichment
        if not metadata.get("detected_type") or metadata["detected_type"] == "unknown":
            print("⚠️ Running backup classifier due to unknown document type...")
            text = _extract_text_pdfminer(pdf_path) or _extract_text_ocr(pdf_path)
            classification = classify_document_type(text)
            metadata["detected_type"] = classification.get("type", "unknown")
            metadata["confidence"] = max(
                metadata.get("confidence", 0.0),
                classification.get("confidence", 0.0),
            )

        # Step 4: Final normalization
        metadata["confidence"] = round(float(metadata.get("confidence", 0.0)), 2)
        if not metadata.get("name") and not metadata.get("pan"):
            metadata["status"] = "partial_extraction"
        else:
            metadata["status"] = "ok"

        return metadata

    except Exception as e:
        print(f"❌ Critical failure in classify_and_extract_metadata: {e}")
        return {
            "detected_type": "unknown",
            "confidence": 0.0,
            "name": None,
            "pan": None,
            "fy": None,
            "ay": None,
            "employer": None,
            "employer_pan": None,
            "error": str(e),
            "status": "failed",
        }
