# backend/services/text_cleaner.py
# Python 3.9+ Compatible, production-ready OCR text cleaner

import re
import unicodedata
from typing import Optional, List

# --------------------------------------------------------------------
# 🔹 Regex Definitions
# --------------------------------------------------------------------
PAN_RE = re.compile(r"\b([A-Z]{5}\d{4}[A-Z])\b")
AY_RE = re.compile(r"\b(20\d{2})\s*[-/–]\s*(\d{2})\b")
FY_RE = re.compile(r"\b(?:FY\s*)?(20\d{2})\s*[-/–]\s*(\d{2})\b", re.IGNORECASE)

# Common junk tokens that look like “names” in OCR but aren’t
NOISE_TOKENS = {
    "CERTIFICATE", "CERTIFICATE NO", "SR", "SR.", "NO", "NO.",
    "AMOUNT", "STATUS", "DESCRIPTION", "INFORMATION", "REPORTED",
    "UNMATCHED", "MATCHED", "DEPOSITED", "DEDUCTED", "CREDIT",
    "SECTION", "U/S", "FORM", "FORM NO", "PART", "A", "B",
    "FY", "AY", "YEAR", "DATE", "PLACE", "SIGNATURE",
    "UNDER", "SENIOR", "CITIZEN", "SPECIFIED"
}

# ✅ Add this helper function (required by semantic_extractor)
def is_pan(s: str) -> bool:
    """
    Check if the given string matches Indian PAN format (ABCDE1234F).
    """
    if not s:
        return False
    return bool(PAN_RE.fullmatch(s.strip().upper()))
# --------------------------------------------------------------------
# 🔹 Base Utilities
# --------------------------------------------------------------------
def normalize_spaces(s: str) -> str:
    """Normalize whitespace and remove zero-width / control characters."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.category(ch).startswith("C"))
    s = re.sub(r"\s+", " ", s).strip()
    return s


def clean_text_lines(text: str) -> List[str]:
    """Split and clean text into usable lines."""
    lines = []
    for line in text.splitlines():
        line = normalize_spaces(line)
        if not line or line.isdigit():
            continue
        if len(line) < 3:
            continue
        lines.append(line)
    return lines


# --------------------------------------------------------------------
# 🔹 PAN and FY/AY utilities
# --------------------------------------------------------------------
def extract_first_pan(text: str) -> Optional[str]:
    """Extract the first valid PAN (high precision)."""
    if not text:
        return None
    matches = PAN_RE.findall(text.upper())
    for m in matches:
        # Skip likely employer PANs (e.g., with “AABCF…” prefixes common to companies)
        if not m.startswith("AAAA") and not m.endswith("ZZ"):
            return m
    return matches[0] if matches else None


def derive_fy_from_ay(ay: str) -> Optional[str]:
    m = AY_RE.search(ay or "")
    if not m:
        return None
    y_start = int(m.group(1))
    y_end2 = int(m.group(2))
    return f"{y_start-1}-{y_end2-1:02d}"


def pick_fy(text: str) -> Optional[str]:
    """Find FY if explicitly mentioned, else derive from AY."""
    if not text:
        return None
    m_fy = FY_RE.search(text)
    if m_fy:
        return f"{m_fy.group(1)}-{m_fy.group(2)}"
    m_ay = AY_RE.search(text)
    if m_ay:
        return derive_fy_from_ay(m_ay.group(0))
    return None


# --------------------------------------------------------------------
# 🔹 Name detection heuristics
# --------------------------------------------------------------------
def looks_like_name(token: str) -> bool:
    """
    Determine if a token is a plausible person name:
    - Only alphabetic and space
    - Not a known noise token
    - At least 2 words or >= 4 chars
    """
    if not token:
        return False

    t = normalize_spaces(token).upper()
    if len(t) < 4 or not re.fullmatch(r"[A-Z\s\.]+", t):
        return False

    if t in NOISE_TOKENS:
        return False
    if any(x in t for x in ["FORM", "CERTIFICATE", "PART ", "SECTION", "DESCRIPTION"]):
        return False

    words = t.split()
    if len(words) == 1 and len(words[0]) < 4:
        return False

    return True


def sanitize_candidate_name(s: str) -> Optional[str]:
    """Normalize and validate candidate name."""
    if not s:
        return None

    s = normalize_spaces(re.sub(r"[^A-Z\s\.]", " ", s.upper()))
    s = s.strip(". ")
    if not looks_like_name(s):
        return None

    # remove double initials like “P PNEF.” -> “P PNEF”
    s = re.sub(r"\b([A-Z])\b(?!\.)", r"\1", s)
    s = normalize_spaces(s)
    return s or None


def find_nearest_name_around_pan(text: str, pan: Optional[str]) -> Optional[str]:
    """
    Extract name near the PAN position in text (smart fallback when LLM fails).
    """
    if not text or not pan:
        return None

    lines = clean_text_lines(text)
    for i, line in enumerate(lines):
        if pan in line:
            window = " ".join(lines[max(0, i-3):i+3])
            candidates = re.findall(r"[A-Z][A-Z\s\.]{3,40}", window)
            for c in candidates:
                cand = sanitize_candidate_name(c)
                if cand:
                    return cand
    return None


# --------------------------------------------------------------------
# 🔹 Public API
# --------------------------------------------------------------------
__all__ = [
    "normalize_spaces",
    "clean_text_lines",
    "extract_first_pan",
    "derive_fy_from_ay",
    "pick_fy",
    "looks_like_name",
    "sanitize_candidate_name",
    "find_nearest_name_around_pan",
    "is_pan",   # ✅ add this line
]
