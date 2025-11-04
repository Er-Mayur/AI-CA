# backend/services/structured_extractor.py
# -------------------------------------------------------------
# Production-grade structured extractor (deterministic fallback)
# -------------------------------------------------------------
import re
from typing import Dict, Optional, Tuple

# --------------------------------------------------------------------
# 1️⃣ Regex primitives
# --------------------------------------------------------------------
_BAD_NAME_TOKENS = re.compile(
    r"(?i)\b(CERTIFICATE|FORM|SECTION|SENIOR|SPECIFIED|SUB-SECTION|CHAPTER|PART|SCHEDULE|ANNEXURE|ANNEX|NOTE|DECLARATION|INDIA|PRIVATE|LIMITED|LTD|PVT|BANK|ACCOUNT|ADDRESS|EMPLOYER|EMPLOYEE|ASSESSMENT|FINANCIAL|YEAR|PAN|TAN|DESCRIPTION|INFORMATION|REPORTED|AMOUNT|STATUS)\b"
)
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_FY_RE = re.compile(r"(?:Financial\s*Year|FY)\s*[:\-]?\s*(20\d{2})[-–](\d{2})", re.I)
_AY_RE = re.compile(r"(?:Assessment\s*Year|AY)\s*[:\-]?\s*(20\d{2})[-–](\d{2})", re.I)


# --------------------------------------------------------------------
# 2️⃣ Utility cleaners
# --------------------------------------------------------------------
def _safe_caps(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s


def _title_case_if_name(cand: str) -> Optional[str]:
    cand = _safe_caps(cand.upper())
    if len(cand.split()) < 2:
        return None
    if _BAD_NAME_TOKENS.search(cand):
        return None
    if re.match(r"^[A-Z]\s+[A-Z]{3,}$", cand):  # like "P PNEF"
        return None
    return cand.title()


# --------------------------------------------------------------------
# 3️⃣ Document type detection
# --------------------------------------------------------------------
def detect_doc_type(text: str) -> Tuple[str, float]:
    t = text.lower()
    if re.search(r"form\s*no\.?\s*16", t) or "certificate under section 203" in t:
        return "form 16", 0.98
    if re.search(r"\bform\s*26as\b", t) or "tax credit statement" in t:
        return "form 26as", 0.98
    if re.search(r"\bannual\s+information\s+statement\b", t) or "ais" in t:
        return "ais", 0.98
    return "unknown", 0.8


# --------------------------------------------------------------------
# 4️⃣ FY / AY extraction
# --------------------------------------------------------------------
def extract_fy_ay(text: str) -> Tuple[Optional[str], Optional[str]]:
    fy = ay = None
    mfy, may = _FY_RE.search(text), _AY_RE.search(text)
    if mfy:
        fy = f"{mfy.group(1)}-{mfy.group(2)}"
    if may:
        ay = f"{may.group(1)}-{may.group(2)}"
    if not fy and may:
        fy = f"{int(may.group(1)) - 1}-{(int(may.group(2)) - 1):02d}"
    return fy, ay


# --------------------------------------------------------------------
# 5️⃣ PAN extraction
# --------------------------------------------------------------------
def extract_pans(text: str) -> Tuple[Optional[str], Optional[str]]:
    pans = _PAN_RE.findall(text)
    if not pans:
        return None, None
    if len(pans) >= 2:
        return pans[0], pans[1]  # (employer, employee)
    return None, pans[0]


# --------------------------------------------------------------------
# 6️⃣ Name heuristics
# --------------------------------------------------------------------
def _extract_after_employee_block(text: str) -> Optional[str]:
    block = re.search(
        r"(?is)(Name\s+and\s+address\s+of\s+the\s+Employee[^\n]*)(?:\n+)([^\n]+)", text
    ) or re.search(
        r"(?is)(Name\s+and\s+address\s+of\s+the\s+Employee\s*/\s*Specified\s+senior\s+citizen[^\n]*)(?:\n+)([^\n]+)",
        text,
    )
    if block:
        return _title_case_if_name(block.group(2))
    return None


def _nearest_caps_before(text: str, anchor: str, win: int = 400) -> Optional[str]:
    if not anchor:
        return None
    idx = text.find(anchor)
    if idx == -1:
        return None
    window = text[max(0, idx - win): idx]
    caps = re.findall(r"[A-Z][A-Z\s\.\-&']{5,}", window)
    caps = [c for c in map(_safe_caps, caps) if len(c.split()) >= 2 and not _BAD_NAME_TOKENS.search(c)]
    if caps:
        return caps[-1].title()
    return None


def extract_employer_name(text: str) -> Optional[str]:
    m = re.search(r"(?i)Name\s+and\s+address\s+of\s+the\s+Employer[^\n]*\n+([A-Z][A-Z\s\.\-&']+)", text)
    if m:
        cand = _title_case_if_name(m.group(1))
        if cand:
            return cand
    # fallback for company names anywhere
    for ln in text.splitlines():
        L = ln.strip().upper()
        if re.search(r"(PRIVATE|LIMITED|LTD|PVT|INDIA)", L) and len(L.split()) >= 2:
            return L.title()
    return None


def extract_employee_name(text: str, employee_pan: Optional[str]) -> Optional[str]:
    name = _extract_after_employee_block(text)
    if name:
        return name
    m = re.search(r"(?i)Employee\s*Name[:\-]?\s*([A-Z][A-Z\s\.\-&']+)", text)
    if m:
        cand = _title_case_if_name(m.group(1))
        if cand:
            return cand
    if employee_pan:
        near = _nearest_caps_before(text, employee_pan)
        if near:
            return near
    return None


# --------------------------------------------------------------------
# 7️⃣ Master extractor
# --------------------------------------------------------------------
def extract_structured(text: str) -> Dict[str, Optional[str]]:
    doc_type, doc_conf = detect_doc_type(text)
    fy, ay = extract_fy_ay(text)
    employer_pan, employee_pan = extract_pans(text)
    employer = extract_employer_name(text)
    employee = extract_employee_name(text, employee_pan)

    # sanity post-filters
    if employee and _BAD_NAME_TOKENS.search(employee.upper()):
        employee = None
    if employer and not re.search(r"(PRIVATE|LIMITED|LTD|PVT|INDIA)", employer.upper()):
        employer = None

    return {
        "detected_type": doc_type,
        "confidence": doc_conf,
        "name": employee,
        "pan": employee_pan,
        "fy": fy,
        "ay": ay,
        "employer": employer,
        "employer_pan": employer_pan,
    }
