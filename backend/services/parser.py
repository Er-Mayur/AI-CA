# backend/services/parser.py
# -------------------------------------------------------------
# Production-grade Document Verification Engine
# -------------------------------------------------------------
import re
from typing import Tuple, Dict, Any
from fuzzywuzzy import fuzz
from services.llm_client import classify_document_type, extract_text_from_pdf
from services.semantic_extractor import extract_metadata_from_pdf_path
from services.text_cleaner import normalize_spaces, sanitize_candidate_name, find_nearest_name_around_pan


# --------------------------------------------------------------------
# 1️⃣ Utility: normalize name
# --------------------------------------------------------------------
def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.upper()
    name = re.sub(r"[^A-Z\s]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


# --------------------------------------------------------------------
# 2️⃣ Utility: fuzzy name matcher
# --------------------------------------------------------------------
def is_name_match(user_name: str, doc_name: str, threshold: int = 68) -> Tuple[bool, int]:
    if not user_name or not doc_name:
        return (False, 0)

    reg = normalize_name(user_name)
    ext = normalize_name(doc_name)
    score = max(fuzz.token_sort_ratio(reg, ext), fuzz.partial_ratio(reg, ext))

    reg_tokens = reg.split()
    ext_tokens = ext.split()

    # first/last or prefix match
    first_last_match = (
        len(reg_tokens) >= 2 and len(ext_tokens) >= 2 and
        reg_tokens[0] == ext_tokens[0] and reg_tokens[-1] == ext_tokens[-1]
    )
    prefix_match = reg_tokens and ext_tokens and ext_tokens[0].startswith(reg_tokens[0])
    overlap = len(set(reg_tokens) & set(ext_tokens))

    is_match = score >= threshold or first_last_match or prefix_match or overlap >= 2
    return is_match, score


# --------------------------------------------------------------------
# 3️⃣ Core verification routine
# --------------------------------------------------------------------
def verify_document(file_path: str, doc_type: str, user, expected_fy: str) -> Dict[str, Any]:
    """
    🔍 Multi-layer document verification pipeline:
      1. Extract metadata (semantic + layout-aware)
      2. Validate PAN, FY, Name, Document Type
      3. Auto-correct name if OCR/LLM missed it
      4. Produce confidence-weighted structured output
    """
    print(f"📄 Verifying document for user={getattr(user, 'name', 'Unknown')} | FY={expected_fy}")

    # Step 1: Metadata extraction
    metadata = extract_metadata_from_pdf_path(file_path)

    # Step 2: fallback doc-type classification if missing
    if not metadata.get("detected_type") or metadata["detected_type"] == "unknown":
        text = extract_text_from_pdf(file_path)
        classification = classify_document_type(text or "")
        metadata["detected_type"] = classification.get("type", "unknown").lower()
        metadata["confidence"] = max(
            metadata.get("confidence", 0.0),
            classification.get("confidence", 0.0),
        )

    # Step 3: Initialize checks
    issues = []
    name_similarity = None

    # 3a) Document type validation
    if metadata.get("detected_type") and metadata["detected_type"].lower() != doc_type.lower():
        issues.append(f"File appears to be {metadata['detected_type']} not {doc_type}.")

    # 3b) PAN consistency check
    doc_pan = (metadata.get("pan") or "").upper()
    user_pan = (getattr(user, "pan_number", "") or "").upper()
    if not doc_pan:
        issues.append("No PAN detected in document.")
    elif user_pan and doc_pan != user_pan:
        issues.append("PAN mismatch between document and user profile.")

    # 3c) Financial Year check
    fy = normalize_spaces(metadata.get("fy") or "")
    if not fy:
        issues.append("Financial Year not detected in document.")
    elif expected_fy.replace(" ", "") not in fy.replace(" ", ""):
        issues.append(f"Document FY {fy or 'Unknown'} doesn’t match selected FY {expected_fy}.")

    # 3d) Name verification
    doc_name = sanitize_candidate_name(metadata.get("name"))
    if not doc_name:
        # auto-recover name from text using PAN window
        if metadata.get("pan"):
            recovered = find_nearest_name_around_pan(
                normalize_spaces(extract_text_from_pdf(file_path)), metadata["pan"]
            )
            if recovered:
                doc_name = recovered
                metadata["name"] = recovered
                print(f"🧠 Auto-recovered name → {recovered}")
            else:
                issues.append("Employee name not found in document.")
        else:
            issues.append("Employee name not found in document.")
    else:
        m, name_similarity = is_name_match(user.name or "", doc_name)
        if not m:
            issues.append(
                f"Document name does not match registered user (similarity={name_similarity}%)."
            )

    # ----------------------------------------------------------------
    # Step 4: Confidence calibration
    # ----------------------------------------------------------------
    issue_weight = 0.15
    confidence = round(max(0.35, 1 - issue_weight * len(issues)), 2)

    # Step 5: Verification summary
    verified = len(issues) == 0
    result = {
        "verified": verified,
        "confidence": confidence,
        "issues": issues,
        "metadata": metadata,
        "name_similarity": name_similarity,
    }

    # Structured logging for devops monitoring
    print(f"🧠 Verification Summary (user={user.name}):")
    print(json_safe(result))
    return result


# --------------------------------------------------------------------
# 4️⃣ Helper for clean console output
# --------------------------------------------------------------------
def json_safe(obj: Any) -> str:
    import json
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)
