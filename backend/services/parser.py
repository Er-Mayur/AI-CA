# backend/services/parser.py
import re
from fuzzywuzzy import fuzz
from services.llm_client import classify_and_extract_metadata


# ---------------------------------------------------------------
# 🔹 Utility Normalizer
# ---------------------------------------------------------------
def normalize_name(name: str) -> str:
    """Normalize name for case, spacing, and special chars."""
    if not name:
        return ""
    name = name.upper()
    name = re.sub(r"[^A-Z\s]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


# ---------------------------------------------------------------
# 🔹 Smart Fuzzy Name Matcher
# ---------------------------------------------------------------
def is_name_match(user_name: str, doc_name: str, threshold: int = 65) -> tuple[bool, int]:
    """
    Enhanced name matcher:
    ✅ Ignores middle names or initials.
    ✅ Uses fuzzy, token overlap, and prefix matching.
    """
    if not user_name or not doc_name:
        return False, 0

    reg = normalize_name(user_name)
    ext = normalize_name(doc_name)

    score = max(fuzz.token_sort_ratio(reg, ext), fuzz.partial_ratio(reg, ext))
    reg_tokens = reg.split()
    ext_tokens = ext.split()

    # first & last match rule
    first_last_match = False
    if len(reg_tokens) >= 2 and len(ext_tokens) >= 2:
        first_last_match = reg_tokens[0] == ext_tokens[0] and reg_tokens[-1] == ext_tokens[-1]

    # prefix rule (e.g., "NITIN" vs "NITIN BHAGIRATH")
    prefix_match = reg_tokens and ext_tokens and ext_tokens[0].startswith(reg_tokens[0])

    # overlap rule (e.g., NITIN + PANDE both appear)
    overlap = len(set(reg_tokens) & set(ext_tokens))

    print(f"🧩 Comparing: {reg} ↔ {ext} | score={score}, overlap={overlap}, first_last={first_last_match}, prefix={prefix_match}")

    is_match = score >= threshold or first_last_match or prefix_match or overlap >= 2
    return is_match, score


# ---------------------------------------------------------------
# 🔹 Document Verifier
# ---------------------------------------------------------------
def verify_document(file_path: str, doc_type: str, user, expected_fy: str):
    """Verify uploaded document metadata vs user profile."""
    metadata = classify_and_extract_metadata(file_path)
    issues = []
    name_similarity = None

    # 1️⃣ Type
    if metadata["detected_type"] and metadata["detected_type"].lower() != doc_type.lower():
        issues.append(f"File appears to be {metadata['detected_type']} not {doc_type}.")

    # 2️⃣ PAN
    if metadata.get("pan"):
        user_pan = getattr(user, "pan_number", None)
        if not user_pan:
            issues.append("User PAN missing in profile.")
        elif metadata["pan"].upper() != user_pan.upper():
            issues.append("PAN mismatch between document and user profile.")
    else:
        issues.append("No PAN detected in document.")

    # 3️⃣ FY
    if metadata.get("fy"):
        fy_norm = metadata["fy"].replace("FY", "").strip()
        if expected_fy not in fy_norm:
            issues.append(f"Document FY {metadata['fy']} doesn’t match selected FY {expected_fy}.")
    else:
        issues.append("Financial Year not detected in document.")

    # 4️⃣ Name check
    if metadata.get("name"):
        match, name_similarity = is_name_match(user.name, metadata["name"])
        if not match:
            issues.append(f"Document name does not match registered user (similarity={name_similarity}%).")
    else:
        issues.append("Employee name not found in document.")

    # ✅ Final Verdict
    verified = len(issues) == 0
    confidence = round(max(0.0, 1 - 0.15 * len(issues)), 2)

    result = {
        "verified": verified,
        "confidence": confidence,
        "issues": issues,
        "metadata": metadata,
        "name_similarity": name_similarity
    }

    print("🧠 Verification Summary:", result)
    return result

