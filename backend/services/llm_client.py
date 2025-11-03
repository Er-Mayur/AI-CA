# backend/services/llm_client.py
import os
import re
import pytesseract
import torch
from typing import Dict
from pdf2image import convert_from_path
from transformers import pipeline
from fuzzywuzzy import fuzz
from core.config import TESSERACT_PATH, POPPLER_PATH
from services.semantic_extractor import extract_metadata_from_text

# --------------------------------------------------------------------
# 0️⃣ macOS / Hardware setup
# --------------------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
DEVICE = 0 if torch.backends.mps.is_available() else -1
print(f"🚀 Using device: {'Apple MPS GPU' if DEVICE == 0 else 'CPU'}")

# --------------------------------------------------------------------
# 1️⃣ Lazy pipeline init
# --------------------------------------------------------------------
CLASSIFIER = None
NER = None

def _ensure_pipelines():
    global CLASSIFIER, NER
    if CLASSIFIER and NER:
        return
    try:
        print("⏳ Loading Hugging Face models ...")
        CLASSIFIER = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=DEVICE)
        NER = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple", device=DEVICE)
        print("✅ Pipelines ready.")
    except Exception as e:
        print(f"⚠️ Pipeline init failed: {e}")

# --------------------------------------------------------------------
# 2️⃣ Text Extraction (PDFMiner → OCR fallback)
# --------------------------------------------------------------------
def _extract_text_pdfminer(pdf_path: str) -> str:
    try:
        from pdfminer.high_level import extract_text
        txt = extract_text(pdf_path) or ""
        return txt.replace("\x00", "")
    except Exception as e:
        print(f"⚠️ pdfminer failed: {e}")
        return ""

def _extract_text_ocr(pdf_path: str, dpi: int = 300) -> str:
    try:
        pages = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=3, poppler_path=POPPLER_PATH)
        text = "\n".join([pytesseract.image_to_string(p) for p in pages])
        return text
    except Exception as e:
        print(f"⚠️ OCR fallback failed: {e}")
        return ""

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Hybrid extractor with auto-cleaning & standardized OCR debug filename.
    NOTE: The OCR text is saved *next to the provided pdf_path* by appending '_ocr_text.txt'.
    This works with staged paths; promotion to final names is done in the API layer after verification.
    """
    text = _extract_text_pdfminer(pdf_path)
    if not text or len(text.strip()) < 100:
        text = _extract_text_ocr(pdf_path)

    text = text.replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    noise = ["Signature", "Responsible", "Full Name", "Place", "Date"]
    clean = [ln for ln in lines if not any(re.search(n, ln, re.IGNORECASE) for n in noise)]
    text = "\n".join(clean)

    # Save OCR text *beside* the given pdf_path
    try:
        dir_name = os.path.dirname(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        ocr_name = f"{base_name}_ocr_text.txt" if not base_name.endswith("_ocr_text") else f"{base_name}.txt"
        ocr_path = os.path.join(dir_name, ocr_name)

        with open(ocr_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"🧾 OCR text saved → {ocr_path} ({len(text)} chars)")
    except Exception as e:
        print(f"⚠️ Debug save failed: {e}")

    return text

# --------------------------------------------------------------------
# 3️⃣ Type Classifier (rule + fuzzy + ML)
# --------------------------------------------------------------------
def classify_document_type(text: str) -> Dict[str, object]:
    if not text:
        return {"type": "unknown", "confidence": 0.0}
    txt = text.lower()

    fuzzy_16 = fuzz.partial_ratio("form 16", txt)
    fuzzy_26 = fuzz.partial_ratio("form 26as", txt)
    fuzzy_ais = fuzz.partial_ratio("annual information statement", txt)

    if re.search(r"form\s*no\.?\s*16", txt) or "certificate under section 203" in txt or fuzzy_16 > 80:
        return {"type": "form 16", "confidence": 0.98}
    if re.search(r"form\s*26as", txt) or "tax credit statement" in txt or fuzzy_26 > 80:
        return {"type": "form 26as", "confidence": 0.98}
    if re.search(r"annual\s+information\s+statement", txt) or fuzzy_ais > 80:
        return {"type": "ais", "confidence": 0.98}

    _ensure_pipelines()
    if not CLASSIFIER:
        return {"type": "unknown", "confidence": 0.0}
    try:
        res = CLASSIFIER(text[:1500], ["Form 16", "Form 26AS", "AIS"])
        return {"type": res["labels"][0].lower(), "confidence": float(res["scores"][0])}
    except Exception as e:
        print(f"⚠️ classify_document_type error: {e}")
        return {"type": "unknown", "confidence": 0.0}

# --------------------------------------------------------------------
# 4️⃣ Regex-based Entity Extractor (for fallback)
# --------------------------------------------------------------------
def _regex_entities(text: str) -> dict:
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.split("\n") if l.strip()]
    flat = " ".join(lines)

    name = pan = fy = ay = employer = None
    employer_pan = None  # initialize

    all_pans = re.findall(r"\b[A-Z]{5}\d{4}[A-Z]\b", flat)
    if all_pans:
        if len(all_pans) >= 2:
            employer_pan = all_pans[0]
            pan = all_pans[1]
        else:
            pan = all_pans[0]

    name_match = re.search(r"Name\s+and\s+address\s+of\s+the\s+Employee[:\-]?\s*([A-Z\s]+)", flat, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip().upper()
    if not name:
        for i, line in enumerate(lines):
            if "employee" in line.lower() and i + 1 < len(lines):
                candidate = lines[i + 1]
                if not re.search(r"(PRIVATE|LIMITED|PVT|INDIA|FORM|HITACHI)", candidate, re.IGNORECASE):
                    name = candidate.strip().upper()
                    break

    employer_match = re.search(r"Name\s+and\s+address\s+of\s+the\s+Employer[:\-]?\s*([A-Z\s]+)", flat, re.IGNORECASE)
    if employer_match:
        employer = employer_match.group(1).strip().upper()
    else:
        for line in lines:
            if re.search(r"(PRIVATE|LIMITED|PVT|LTD)", line, re.IGNORECASE):
                employer = line.strip().upper()
                break

    fy_match = re.search(r"(?:Financial\s*Year|FY)\s*[:\-]?\s*(20\d{2})[-–](\d{2})", flat, re.IGNORECASE)
    ay_match = re.search(r"(?:Assessment\s*Year|AY)\s*[:\-]?\s*(20\d{2})[-–](\d{2})", flat, re.IGNORECASE)

    if fy_match:
        fy = f"{fy_match.group(1)}-{fy_match.group(2)}"
    if ay_match:
        ay = f"{ay_match.group(1)}-{ay_match.group(2)}"
    if not fy and ay_match:
        start_year = int(ay_match.group(1)) - 1
        end_year = int(ay_match.group(2)) - 1
        fy = f"{start_year}-{end_year:02d}"

    return {
        "name": name,
        "pan": pan,
        "fy": fy,
        "ay": ay,
        "employer": employer,
        "employer_pan": employer_pan,
    }

# --------------------------------------------------------------------
# 5️⃣ Unified Extractor (OCR → rules → A4F)
# --------------------------------------------------------------------
def classify_and_extract_metadata(pdf_path: str) -> dict:
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "detected_type": "unknown",
            "confidence": 0.0,
            "pan": None,
            "fy": None,
            "ay": None,
            "name": None,
            "employer": None
        }

    doc = classify_document_type(text)
    regex_meta = _regex_entities(text)

    try:
        ai_meta = extract_metadata_from_text(text)
        for k, v in regex_meta.items():
            if not ai_meta.get(k) and v:
                ai_meta[k] = v
        return {
            "detected_type": ai_meta.get("detected_type", doc["type"]),
            "confidence": ai_meta.get("confidence", doc["confidence"]),
            "name": ai_meta.get("name"),
            "pan": ai_meta.get("pan"),
            "fy": ai_meta.get("fy"),
            "ay": ai_meta.get("ay"),
            "employer": ai_meta.get("employer"),
            "employer_pan": ai_meta.get("employer_pan"),
        }
    except Exception as e:
        print(f"⚠️ Semantic extractor failed: {e}")
        return {
            "detected_type": doc["type"],
            "confidence": doc["confidence"],
            **regex_meta
        }
