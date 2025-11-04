# backend/services/semantic_extractor.py
# Hybrid semantic + layout-aware extractor (Ollama local → A4F fallback)

import json
from typing import Any, Dict, Optional
from core.config import (
    a4f_client, A4F_MODEL,
    ollama_client, OLLAMA_MODEL,
    USE_OLLAMA
)
from services.layout_ocr import (
    ocr_words_from_pdf, words_to_lines, lines_to_text, detect_tables
)
from services.text_cleaner import (
    normalize_spaces,
    extract_first_pan,
    pick_fy,
    sanitize_candidate_name,
    find_nearest_name_around_pan,
    is_pan,
)

# --------------------------------------------------------------------
# 🔹 Step 1: Build compact layout context
# --------------------------------------------------------------------
def _build_structured_layout_text(pdf_path: str) -> Dict[str, Any]:
    pages = ocr_words_from_pdf(pdf_path, dpi=300, max_pages=5)
    layout = {"pages": []}

    for p in pages:
        lines = words_to_lines(p.get("words", []))
        text_lines = lines_to_text(lines)
        tables = detect_tables(lines)
        layout["pages"].append({
            "page": p["page"],
            "text_lines": text_lines[:120],
            "tables": tables[:3],
            "size": p["size"],
        })

    raw_preview = "\n".join(ln for pg in layout["pages"] for ln in pg["text_lines"])
    hint_pan = extract_first_pan(raw_preview)
    hint_fy = pick_fy(raw_preview)

    return {
        "layout": layout,
        "raw_preview": raw_preview[:12000],
        "hint_pan": hint_pan,
        "hint_fy": hint_fy,
    }


# --------------------------------------------------------------------
# 🔹 Step 2: Unified extractor (prefers Ollama, falls back to A4F)
# --------------------------------------------------------------------
def extract_metadata_from_pdf_path(pdf_path: str) -> Dict[str, Any]:
    pack = _build_structured_layout_text(pdf_path)
    raw_preview, hint_pan, hint_fy = (
        pack["raw_preview"], pack["hint_pan"], pack["hint_fy"]
    )

    prompt = f"""
You are an expert parser for Indian income-tax forms (Form 16, Form 26AS, AIS).

Return STRICT JSON:

{{
  "Document Type": "Form 16 | Form 26AS | AIS | Unknown",
  "Employee Name": "",
  "Employee PAN": "",
  "Employer Name": "",
  "Employer PAN": "",
  "Assessment Year": "",
  "Financial Year": ""
}}

Rules:
- Identify both PANs (employer first, employee second).
- Derive FY from AY if missing.
- If 'FORM NO. 16' or 'Section 203' appears → Document Type = "Form 16".
- Output ONLY JSON.

Document text:
{raw_preview[:8000]}
"""

    # -----------------------
    # 🧠 1. Try local Ollama
    # -----------------------
    if USE_OLLAMA and ollama_client:
        try:
            print(f"🧩 Using local Ollama model: {OLLAMA_MODEL}")
            resp = ollama_client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": "You extract structured data from tax documents precisely."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=800,
            )
            raw_out = resp.choices[0].message.content.strip()
            result = _safe_json_load(raw_out)
            return _postprocess_result(result, raw_preview, hint_pan, hint_fy)

        except Exception as e:
            print(f"⚠️ Ollama extraction failed ({e}) — switching to A4F cloud fallback...")

    # -----------------------
    # ☁️ 2. Fallback to A4F
    # -----------------------
    if a4f_client:
        try:
            print(f"🧩 Using A4F model: {A4F_MODEL}")
            resp = a4f_client.chat.completions.create(
                model=A4F_MODEL,
                messages=[
                    {"role": "system", "content": "You extract tax document metadata precisely."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=800,
            )
            raw_out = resp.choices[0].message.content.strip()
            result = _safe_json_load(raw_out)
            return _postprocess_result(result, raw_preview, hint_pan, hint_fy)
        except Exception as e:
            print(f"⚠️ A4F extraction failed: {e}")
            return _fallback_local(raw_preview, hint_pan, hint_fy, str(e))

    # -----------------------
    # ❌ 3. Both failed
    # -----------------------
    return _fallback_local(raw_preview, hint_pan, hint_fy, "No AI model available")


# --------------------------------------------------------------------
# 🔹 Step 3: Helpers
# --------------------------------------------------------------------
def _safe_json_load(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        snippet = raw[raw.find("{"):raw.rfind("}") + 1]
        return json.loads(snippet) if snippet else {}


def _postprocess_result(result: dict, raw_preview: str,
                        hint_pan: Optional[str], hint_fy: Optional[str]) -> Dict[str, Any]:
    doc_type = (result.get("Document Type") or "Unknown").strip()
    emp_name = sanitize_candidate_name(result.get("Employee Name") or "")
    emp_pan = (result.get("Employee PAN") or "").strip().upper()
    org_name = sanitize_candidate_name(result.get("Employer Name") or "")
    org_pan = (result.get("Employer PAN") or "").strip().upper()
    ay = normalize_spaces(result.get("Assessment Year") or "")
    fy = normalize_spaces(result.get("Financial Year") or "")

    # PAN sanity
    if emp_pan and not is_pan(emp_pan):
        if is_pan(org_pan):
            emp_pan, org_pan = org_pan, emp_pan
        elif hint_pan:
            emp_pan = hint_pan
    if org_pan and not is_pan(org_pan):
        org_pan = None

    # FY fallback
    if not fy and hint_fy:
        fy = hint_fy

    # Name recovery
    if not emp_name or emp_name in ["CERTIFICATE NO", "CERTIFICATE", "SR NO"]:
        print(f"⚠️ Auto-correcting invalid AI name '{emp_name}' → regex fallback")
        emp_name = find_nearest_name_around_pan(raw_preview, emp_pan)

    confidence = 0.98 if doc_type.lower() in ["form 16", "form 26as", "ais"] else 0.8
    return {
        "detected_type": doc_type.lower(),
        "confidence": confidence,
        "name": emp_name,
        "pan": emp_pan,
        "fy": fy,
        "ay": ay,
        "employer": org_name,
        "employer_pan": org_pan,
    }


# --------------------------------------------------------------------
# 🔹 Step 4: Local fallback
# --------------------------------------------------------------------
def _fallback_local(text: str, hint_pan: Optional[str],
                    hint_fy: Optional[str], err: str) -> Dict[str, Any]:
    print(f"⚠️ Fallback local extractor triggered ({err})")
    name = find_nearest_name_around_pan(text, hint_pan)
    emp_pan = hint_pan
    fy = hint_fy
    doc_type = "unknown"
    low = text.lower()
    if "form 16" in low:
        doc_type = "form 16"
    elif "26as" in low:
        doc_type = "form 26as"
    elif "annual information statement" in low or "ais" in low:
        doc_type = "ais"

    return {
        "detected_type": doc_type,
        "confidence": 0.6,
        "name": name,
        "pan": emp_pan,
        "fy": fy,
        "ay": None,
        "employer": None,
        "employer_pan": None,
        "error": err,
    }


# --------------------------------------------------------------------
# 🔹 Legacy compatibility
# --------------------------------------------------------------------
def extract_metadata_from_text(_: str) -> dict:
    return {
        "detected_type": None,
        "name": None,
        "pan": None,
        "fy": None,
        "ay": None,
        "employer": None,
        "employer_pan": None,
        "confidence": 0.0,
        "note": "Use extract_metadata_from_pdf_path for layout-aware extraction.",
    }


__all__ = ["extract_metadata_from_pdf_path", "extract_metadata_from_text"]
