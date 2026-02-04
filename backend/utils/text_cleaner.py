"""
Text Cleaning and Pattern Extraction Service
Extracts PAN, Name, Financial Year using regex and heuristics
100% offline - deterministic pattern matching
"""

import re
from typing import Optional, Tuple, List, Dict, Any


def normalize_spaces(text: str) -> str:
    """Remove OCR junk and normalize whitespace"""
    # Remove invisible characters
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Normalize multiple spaces to single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_first_pan(text: str) -> Optional[str]:
    """
    Extract first valid PAN using regex
    PAN format: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)
    """
    # Standard PAN pattern
    pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
    match = re.search(pan_pattern, text.upper())
    
    if match:
        return match.group(0)
    
    # Try with possible spaces/special chars
    pan_pattern_loose = r'\b[A-Z]{5}\s*\d{4}\s*[A-Z]\b'
    match = re.search(pan_pattern_loose, text.upper())
    
    if match:
        # Remove spaces
        return match.group(0).replace(' ', '')
    
    return None


def extract_all_pans(text: str) -> List[str]:
    """Extract all PAN numbers from text"""
    pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
    matches = re.findall(pan_pattern, text.upper())
    return list(set(matches))  # Remove duplicates


def pick_fy(text: str, expected_fy: str = None, doc_type: str = None) -> Optional[str]:
    """
    Extract Financial Year or Assessment Year
    Formats: 2024-25, 2024-2025, FY 2024-25, AY 2025-26
    
    IMPORTANT: Financial Year (FY) is one year before Assessment Year (AY)
    Example: FY 2024-25 corresponds to AY 2025-26
    
    Args:
        text: Document text to extract from
        expected_fy: Expected financial year (optional, helps prioritize correct year)
        doc_type: Document type (optional, helps with AIS-specific extraction)
    """
    # Special handling for AIS documents (they have a specific format)
    if doc_type and 'AIS' in doc_type.upper():
        # AIS format: "Financial Year\nAssessment Year\n\n2024-25\n2025-26"
        # We need to find the year that appears right after "Financial Year" label
        ais_fy_pattern = r'Financial\s+Year\s*\n+\s*Assessment\s+Year\s*\n+\s*(\d{4})\s*-\s*(\d{2,4})'
        ais_match = re.search(ais_fy_pattern, text, re.IGNORECASE | re.MULTILINE)
        if ais_match:
            year1 = ais_match.group(1)
            year2 = ais_match.group(2)
            if len(year2) == 4:
                year2 = year2[-2:]
            if int(year2) == (int(year1[-2:]) + 1) % 100:
                fy = f"{year1}-{year2}"
                print(f"[AIS_SPECIFIC] Found Financial Year in AIS format: {fy}")
                if expected_fy and expected_fy.strip() == fy:
                    return fy
                return fy
        
        # Alternative AIS pattern: "Financial Year" on one line, year on next line (even if Assessment Year is in between)
        # Look for pattern: Financial Year\n...\n2024-25 (where 2024-25 is the first year after Financial Year)
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'Financial\s+Year', line, re.IGNORECASE):
                # Look at next few lines for the year
                for j in range(i + 1, min(i + 5, len(lines))):
                    year_match = re.search(r'(\d{4})\s*-\s*(\d{2,4})', lines[j])
                    if year_match:
                        year1 = year_match.group(1)
                        year2 = year_match.group(2)
                        if len(year2) == 4:
                            year2 = year2[-2:]
                        if int(year2) == (int(year1[-2:]) + 1) % 100:
                            fy = f"{year1}-{year2}"
                            # Verify it's not actually an AY (checks if "Assessment Year" is on the same line as the year)
                            if 'ASSESSMENT' in lines[j].upper():
                                continue

                            print(f"[AIS_SPECIFIC] Found Financial Year near label: {fy}")
                            if expected_fy and expected_fy.strip() == fy:
                                return fy
                            return fy
        
        # [REMOVED] The dangerous "Fallback" that blindly trusted expected_fy if found in header
        # This was causing False Positives where AY 2025-26 in header was matched as FY 2025-26
        # Just because "Financial Year" text appeared nearby.
        # Strict pattern matching (Priority 1 & 2) below is safer.
    
    # Priority 1: Explicit Financial Year patterns (preferred)
    # Check header first (first 2000 chars usually contain main FY)
    header_text = text[:2000] if len(text) > 2000 else text
    
    # Priority 1.1: Date Range Pattern (common in Form 16)
    # "From 01-Apr-2024 To 31-Mar-2025" -> FY 2024-25
    # "Period with the Employer... 01-04-2024 to 31-03-2025"
    date_range_patterns = [
        r'(\d{1,2})[\s\-\/](?:Apr|April|\d{2})[\s\-\/](\d{4})\s*(?:to|To|\-)\s*(\d{1,2})[\s\-\/](?:Mar|March|\d{2})[\s\-\/](\d{4})',
        r'From\s*[:\-]?\s*(\d{1,2})[\s\-\/](?:Apr|April|\d{2})[\s\-\/](\d{4})',
    ]
    
    for pattern in date_range_patterns:
        match = re.search(pattern, header_text, re.IGNORECASE)
        if match:
            # If full range found (groups 2 and 4 are years)
            if len(match.groups()) >= 4:
                year_start = int(match.group(2))
                year_end = int(match.group(4))
                
                # Check validity (start year + 1 = end year)
                if year_end == year_start + 1:
                    fy = f"{year_start}-{str(year_end)[-2:]}"
                    print(f"[FY_DATE_RANGE] Found FY from date range: {fy}")
                    # If expected_fy provided and matches, prioritize it
                    if expected_fy and expected_fy.strip() == fy:
                        return fy
                    return fy
            
            # If only start date found near "Period" keyword
            elif len(match.groups()) == 2 and ("PERIOD" in header_text.upper() or "EMPLOYER" in header_text.upper()):
                year_start = int(match.group(2))
                year_end = year_start + 1
                fy = f"{year_start}-{str(year_end)[-2:]}"
                print(f"[FY_DATE_RANGE] Found FY from start date: {fy}")
                if expected_fy and expected_fy.strip() == fy:
                    return fy
                return fy

    fy_patterns = [
        r'FY\s*(\d{4})\s*-\s*(\d{2,4})',
        r'Financial\s+Year\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})',
        r'F\.Y\.\s*(\d{4})\s*-\s*(\d{2,4})',
        r'F\.Y\.\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})',
    ]
    
    # Check header first (most important for AIS documents)
    for pattern in fy_patterns:
        match = re.search(pattern, header_text, re.IGNORECASE)
        if match:
            year1 = match.group(1)
            year2 = match.group(2)
            
            # Normalize to YYYY-YY format
            if len(year2) == 4:
                year2 = year2[-2:]
            
            # Validate year sequence
            if int(year2) == (int(year1[-2:]) + 1) % 100:
                fy = f"{year1}-{year2}"
                # If expected_fy provided and matches, prioritize it
                if expected_fy and expected_fy.strip() == fy:
                    return fy
                # Return first match from header
                return fy
    
    # Check full text
    for pattern in fy_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year1 = match.group(1)
            year2 = match.group(2)
            
            # Normalize to YYYY-YY format
            if len(year2) == 4:
                year2 = year2[-2:]
            
            # Validate year sequence
            if int(year2) == (int(year1[-2:]) + 1) % 100:
                fy = f"{year1}-{year2}"
                # If expected_fy provided and matches, prioritize it
                if expected_fy and expected_fy.strip() == fy:
                    return fy
                # Otherwise return first match
                return fy
    
    # Priority 2: Assessment Year patterns (convert to FY)
    ay_patterns = [
        r'AY\s*(\d{4})\s*-\s*(\d{2,4})',
        r'Assessment\s+Year\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})',
        r'A\.Y\.\s*(\d{4})\s*-\s*(\d{2,4})',
        r'A\.Y\.\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})',
        r'Asst\.?\s*Year\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})', # "Asst. Year"
        r'Asst\s*Year\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})',    # "Asst Year"
    ]
    
    for pattern in ay_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            ay_year1 = int(match.group(1))
            # FY is one year before AY
            # AY 2025-26 → FY 2024-25
            fy_year1 = ay_year1 - 1
            fy_year2 = str(fy_year1 + 1)[-2:]
            fy = f"{fy_year1}-{fy_year2}"
            # If expected_fy provided and matches, prioritize it
            if expected_fy and expected_fy.strip() == fy:
                return fy
            # Otherwise return first match
            return fy
    
    # Priority 2.5: Look for "Financial Year" label followed by year (CRITICAL for AIS)
    # Pattern: "Financial Year" or "FY" followed by year on same or next line
    # Handles AIS format where label and value are on separate lines, even with "Assessment Year" in between
    fy_label_patterns = [
        # AIS Layout 1: Headers aligned with values
        # "Financial Year Assessment Year"
        # "2024-25        2025-26"
        r'Financial\s+Year(?:[\s\S]{0,50}Assessment\s+Year)?[\s\n]+(\d{4})\s*-\s*(\d{2,4})',
        
        # Form 26AS: "Financial Year 2024-25 Assessment Year 2025-26"
        r'Financial\s+Year\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})(?:\s*Assessment\s+Year)',

        r'Financial\s+Year\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})',  # Same line: "Financial Year: 2024-25"
        
        # Next line(s): "Financial Year\n2024-25" 
        # CAREFUL: This was grabbing AY if "Financial Year\nAssessment Year\n2024-25" happened
        # We need to make sure "Assessment Year" is NOT in between if we use this simple multiline match
        # or use a stricter pattern
        r'Financial\s+Year\s*[:\-]?\s*\n+\s*(?!Assessment)(\d{4})\s*-\s*(\d{2,4})',  

        r'Financial\s+Year\s*\n+\s*(\d{4})\s*-\s*(\d{2,4})',  # Next line(s) without separator

        # CRITICAL: Handle AIS/26AS format where "Assessment Year" appears between "Financial Year" and the value
        # This was causing issues if it matched the AY value.
        # But wait, earlier patterns should catch the "Financial Year... value" case first.
        # Let's simple look for explicit Assessment Year patterns and IGNORE them for FY extraction
        
        r'FY\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})',  # FY label
    ]
    
    # Try each pattern and collect matches
    fy_label_matches = []
    for pattern in fy_label_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            year1 = match.group(1) if len(match.groups()) >= 1 else None
            year2 = match.group(2) if len(match.groups()) >= 2 else None
            if year1 and year2:
                # Normalize to YYYY-YY format
                if len(year2) == 4:
                    year2 = year2[-2:]
                # Validate year sequence
                if int(year2) == (int(year1[-2:]) + 1) % 100:
                    fy = f"{year1}-{year2}"
                    fy_label_matches.append((fy, match.start()))
    
    # If we found any FY label matches, prioritize them
    if fy_label_matches:
        # Sort by position (earlier in document = more important)
        fy_label_matches.sort(key=lambda x: x[1])
        # If expected_fy provided, check if it matches any of the label matches
        if expected_fy:
            expected_fy_clean = expected_fy.strip()
            for fy, pos in fy_label_matches:
                if fy == expected_fy_clean:
                    print(f"[FY_LABEL] Found Financial Year label with expected value: {fy}")
                    return fy
        # Return the first (earliest) match
        fy, pos = fy_label_matches[0]
        print(f"[FY_LABEL] Found Financial Year label with value: {fy}")
        return fy
    
    # Priority 2.6: Quick check - if expected_fy is provided, search for it directly first
    # This helps when expected_fy exists but other years are found first
    if expected_fy:
        expected_fy_clean = expected_fy.strip()
        # Look for expected FY in the document
        expected_pattern = rf'\b{re.escape(expected_fy_clean)}\b'
        expected_match = re.search(expected_pattern, text, re.IGNORECASE)
        if expected_match:
            # Check if it's near "Financial Year" label
            start = max(0, expected_match.start() - 300)
            end = min(len(text), expected_match.end() + 300)
            nearby = text[start:end].upper()
            if 'FINANCIAL YEAR' in nearby or ('FINANCIAL' in nearby and 'YEAR' in nearby):
                print(f"[EXPECTED_FY] Found expected FY {expected_fy_clean} near Financial Year label")
                return expected_fy_clean
    
    # Priority 3: Generic year pattern (be careful - could be FY or AY)
    # Only use if no explicit FY/AY label found
    generic_pattern = r'(\d{4})\s*-\s*(\d{2,4})'
    matches = list(re.finditer(generic_pattern, text))
    
    if matches:
        # Collect all valid year ranges
        valid_years = []
        for match in matches:
            year1 = match.group(1)
            year2 = match.group(2)
            
            # Normalize to YYYY-YY format
            if len(year2) == 4:
                year2 = year2[-2:]
            
            # Validate year sequence
            if int(year2) == (int(year1[-2:]) + 1) % 100:
                # Check context (100 chars before and after to catch multi-line labels)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].upper()
                
                # Also check if "Financial Year" appears on the same line or nearby
                # Get the line containing this match
                line_start = text.rfind('\n', 0, match.start())
                line_end = text.find('\n', match.end())
                if line_start == -1:
                    line_start = 0
                if line_end == -1:
                    line_end = len(text)
                line_text = text[line_start:line_end].upper()
                
                # Check if "Financial Year" appears in the same line or within 2 lines
                lines_before = text[max(0, line_start - 200):line_start].upper()
                lines_after = text[line_end:min(len(text), line_end + 200)].upper()
                nearby_text = lines_before + line_text + lines_after
                
                fy = None
                # If context has "ASSESSMENT" or "AY", convert to FY
                # CRITICAL Fix for AIS: AIS often puts "Assessment Year" label above the AY column
                if 'ASSESSMENT' in context or ' AY ' in context or ' A.Y.' in context:
                     # Check if it's explicitly "Financial Year" first though
                     if 'FINANCIAL YEAR' in context and context.index('FINANCIAL YEAR') < context.find(year1):
                         # It's labeled FY, so ignore nearby "Assessment"
                         fy = f"{year1}-{year2}"
                     else:
                        ay_year1 = int(year1)
                        fy_year1 = ay_year1 - 1
                        fy_year2 = str(fy_year1 + 1)[-2:]
                        fy = f"{fy_year1}-{fy_year2}"
                # If context has "FINANCIAL" or "FY", use as-is (CRITICAL for AIS documents)
                elif 'FINANCIAL' in nearby_text or 'FINANCIAL YEAR' in nearby_text or ' FY ' in nearby_text or ' F.Y.' in nearby_text:
                    fy = f"{year1}-{year2}"
                # Default: assume it's FY (most common case)
                else:
                    fy = f"{year1}-{year2}"
                
                if fy:
                    # Track if this match is in header (first 2000 chars)
                    is_in_header = match.start() < 2000
                    # Check if this is near "Financial Year" label (most important)
                    # Use the extended nearby_text for better detection
                    has_fy_label = 'FINANCIAL YEAR' in nearby_text or ('FINANCIAL' in nearby_text and 'YEAR' in nearby_text) or ' FY ' in nearby_text or ' F.Y.' in nearby_text
                    valid_years.append((fy, match.start(), context, is_in_header, has_fy_label))
        
        if valid_years:
            # CRITICAL: If expected_fy provided, prioritize matching years STRONGLY
            if expected_fy:
                expected_fy_clean = expected_fy.strip()
                # First: exact matches with "Financial Year" label in header
                for fy, pos, context, in_header, has_fy_label in valid_years:
                    if fy == expected_fy_clean and in_header and has_fy_label:
                        return fy
                # Second: exact matches with "Financial Year" label anywhere
                for fy, pos, context, in_header, has_fy_label in valid_years:
                    if fy == expected_fy_clean and has_fy_label:
                        return fy
                # Third: exact matches in header
                for fy, pos, context, in_header, has_fy_label in valid_years:
                    if fy == expected_fy_clean and in_header:
                        return fy
                # Fourth: exact matches anywhere
                for fy, pos, context, in_header, has_fy_label in valid_years:
                    if fy == expected_fy_clean:
                        return fy
                # Fifth: close matches (within 1 year) with FY label in header
                expected_match = re.match(r'(\d{4})\s*-\s*(\d{2})', expected_fy_clean)
                if expected_match:
                    expected_year1 = int(expected_match.group(1))
                    for fy, pos, context, in_header, has_fy_label in valid_years:
                        if in_header and has_fy_label:
                            fy_match = re.match(r'(\d{4})\s*-\s*(\d{2})', fy)
                            if fy_match:
                                fy_year1 = int(fy_match.group(1))
                                # If extracted year matches expected or is close, use it
                                if abs(fy_year1 - expected_year1) <= 1:
                                    return fy
            
            # Sort by: FY label priority, header priority, then year (descending - most recent), then position (ascending - earlier in doc)
            valid_years.sort(key=lambda x: (-x[4], -x[3], int(x[0].split('-')[0]), -x[1]), reverse=True)
            
            # FINAL CHECK: If expected_fy is provided and it exists in valid_years, use it even if not perfect match
            if expected_fy and valid_years:
                expected_fy_clean = expected_fy.strip()
                # Check if expected FY exists in the list
                for fy, pos, context, in_header, has_fy_label in valid_years:
                    if fy == expected_fy_clean:
                        print(f"[FALLBACK] Using expected FY {fy} from valid years")
                        return fy
            
            return valid_years[0][0]

    # Priority 4: Final Safety Net - Context-Aware Blind Search for Expected FY/AY
    # If all above failed, but we expect a specific year, look purely for that year string or its AY equivalent
    if expected_fy:
        expected_fy_clean = expected_fy.strip()
        match_exp = re.search(r'(\d{4})[-–](\d{2,4})', expected_fy_clean)
        
        if match_exp:
            y1 = int(match_exp.group(1))
            
            # Check for Expected FY string variants (e.g. "2024-25", "2024-2025", "2024 - 25")
            fy_variants = [
                rf"{y1}\s*[-–]\s*{str(y1+1)[-2:]}",  # 2024-25
                rf"{y1}\s*[-–]\s*{y1+1}",            # 2024-2025
            ]
            
            for pat in fy_variants:
                if re.search(pat, text):
                    print(f"[SAFETY_NET] Found expected FY {expected_fy_clean} (Blind Match)")
                    return expected_fy_clean
            
            # Check for Assessment Year string variants (e.g. "2025-26" -> means FY "2024-25")
            ay1 = y1 + 1
            ay_variants = [
                rf"{ay1}\s*[-–]\s*{str(ay1+1)[-2:]}", # 2025-26
                rf"{ay1}\s*[-–]\s*{ay1+1}",           # 2025-2026
            ]
            
            for pat in ay_variants:
                if re.search(pat, text):
                    print(f"[SAFETY_NET] Found corresponding AY {ay1}-{str(ay1+1)[-2:]} for expected FY {expected_fy_clean} (Blind Match)")
                    return expected_fy_clean
    
    return None


def looks_like_name(token: str) -> bool:
    """Check if token resembles a valid name"""
    if not token:
        return False
    
    # Must be alphabetic (allow spaces)
    if not re.match(r'^[A-Za-z\s\.]+$', token):
        return False
    
    # Reasonable length
    if len(token) < 2 or len(token) > 50:
        return False
    
    # Not a common keyword
    common_keywords = {
        'FORM', 'NO', 'CERTIFICATE', 'UNDER', 'SECTION', 'NAME', 'PAN',
        'DATE', 'FINANCIAL', 'YEAR', 'EMPLOYEE', 'EMPLOYER', 'SALARY',
        'INCOME', 'TAX', 'DEDUCTED', 'SOURCE', 'TDS', 'TOTAL', 'GROSS',
        'NET', 'ASSESSMENT', 'ACKNOWLEDGEMENT', 'RECEIPT', 'PAGE', 'OF'
    }
    
    if token.upper() in common_keywords:
        return False
    
    return True


def find_nearest_name_around_pan(text: str, pan: str) -> Optional[str]:
    """
    Find name near PAN in text
    Strategy: Look for patterns like "Name: JOHN DOE" or "PAN: XXX Name: YYY"
    """
    # Common name labels
    name_patterns = [
        r'Name\s*[:\-]?\s*([A-Z\s\.]{3,50})',
        r'Employee\s+Name\s*[:\-]?\s*([A-Z\s\.]{3,50})',
        r'Assessee\s+Name\s*[:\-]?\s*([A-Z\s\.]{3,50})',
        r'Mr\.\s+([A-Z\s\.]{3,50})',
        r'Mrs\.\s+([A-Z\s\.]{3,50})',
        r'Ms\.\s+([A-Z\s\.]{3,50})',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if looks_like_name(name):
                return normalize_name(name)
    
    return None


def normalize_name(name: str) -> str:
    """Normalize name format"""
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    # Title case
    name = name.strip().title()
    return name


def extract_document_type(text: str) -> Optional[str]:
    """
    Detect document type from text with high precision.
    Uses scoring to resolve ambiguities (e.g. AIS mentioning Form 26AS).
    
    Returns: "Form 16", "Form 26AS", or "AIS"
    """
    text_upper = text.upper()
    
    # Initialize scores
    scores = {
        "Form 16": 0,
        "Form 26AS": 0,
        "AIS": 0
    }
    
    # 1. Header-based Priority Detection (First 1000 chars)
    # The document title is almost always in the header.
    header_text = text_upper[:2000]
    
    if 'ANNUAL INFORMATION STATEMENT' in header_text:
        return "AIS"
    if 'TAXPAYER INFORMATION SUMMARY' in header_text:
        return "AIS"
        
    if 'FORM 26AS' in header_text or 'FORM 26 AS' in header_text:
        return "Form 26AS"
    if 'ANNUAL TAX STATEMENT' in header_text: # Specific to 26AS
        return "Form 26AS"
        
    if 'CERTIFICATE UNDER SECTION 203' in header_text: # Specific to Form 16
        return "Form 16"
    if ('FORM 16' in header_text or 'FORM NO. 16' in header_text) and 'PART A' in header_text:
        return "Form 16"

    # 2. Content-based Scoring (Full text)
    # --- AIS DETECTION ---
    if 'ANNUAL INFORMATION STATEMENT' in text_upper: scores['AIS'] += 10
    if 'TAXPAYER INFORMATION SUMMARY' in text_upper: scores['AIS'] += 10
    if 'AIS' in text_upper and 'SFT INFORMATION' in text_upper: scores['AIS'] += 5
    
    # --- FORM 26AS DETECTION ---
    if 'FORM 26AS' in text_upper or 'FORM 26 AS' in text_upper: scores['Form 26AS'] += 10
    if 'ANNUAL TAX STATEMENT' in text_upper: scores['Form 26AS'] += 10
    if 'TAX CREDIT STATEMENT' in text_upper: scores['Form 26AS'] += 8
    if 'TRACES' in text_upper: scores['Form 26AS'] += 5
    
    # --- FORM 16 DETECTION ---
    if 'CERTIFICATE UNDER SECTION 203' in text_upper: scores['Form 16'] += 10
    if 'FORM 16' in text_upper and ('PART A' in text_upper or 'PART B' in text_upper): scores['Form 16'] += 8
    
    # Negative Signal: If checking for Form 16, but document says "Annual Tax Statement", it's likely 26AS
    if scores['Form 26AS'] > 5 and scores['Form 16'] > 0:
        # Form 16 rarely mentions "Annual Tax Statement" or "TRACES"
        # Form 26AS often mentions "Form 16" in columns
        scores['Form 16'] -= 5

    # Return the one with highest score
    best_match = max(scores, key=scores.get)
    if scores[best_match] > 0:
        return best_match
    
    return None


def extract_verification_data(text: str) -> Dict[str, Any]:
    """
    Master function: Extract all verification data using patterns
    
    Returns:
        {
            'pan': str or None,
            'name': str or None,
            'fy': str or None,
            'doc_type': str or None,
            'all_pans': List[str],
            'confidence': float (0-1)
        }
    """
    # Normalize text
    text_clean = normalize_spaces(text)
    
    # Extract components
    pan = extract_first_pan(text_clean)
    all_pans = extract_all_pans(text_clean)
    fy = pick_fy(text_clean)
    doc_type = extract_document_type(text_clean)
    
    # Find name
    name = None
    if pan:
        name = find_nearest_name_around_pan(text_clean, pan)
    
    if not name:
        # Try generic name extraction
        name = find_nearest_name_around_pan(text_clean, '')
    
    # Calculate confidence
    confidence = 0.0
    if pan:
        confidence += 0.4
    if name:
        confidence += 0.3
    if fy:
        confidence += 0.2
    if doc_type:
        confidence += 0.1
    
    return {
        'pan': pan,
        'name': name,
        'fy': fy,
        'doc_type': doc_type,
        'all_pans': all_pans,
        'confidence': confidence
    }


def names_match(name1: str, name2: str, threshold: float = 0.7) -> bool:
    """
    Check if two names match with fuzzy logic
    
    Args:
        name1: First name
        name2: Second name
        threshold: Match threshold (0-1)
        
    Returns:
        True if names match above threshold
    """
    if not name1 or not name2:
        return False
    
    # Normalize
    n1 = name1.upper().strip()
    n2 = name2.upper().strip()
    
    # Exact match
    if n1 == n2:
        return True
    
    # Split into parts
    parts1 = [p for p in n1.split() if len(p) > 1]
    parts2 = [p for p in n2.split() if len(p) > 1]
    
    if not parts1 or not parts2:
        return False
    
    # Check overlap
    common_parts = set(parts1) & set(parts2)
    max_parts = max(len(parts1), len(parts2))
    
    if max_parts == 0:
        return False
    
    overlap_ratio = len(common_parts) / max_parts
    
    # Match if overlap >= threshold or first+last name match
    if overlap_ratio >= threshold:
        return True
    
    # Check first and last name
    if len(parts1) >= 2 and len(parts2) >= 2:
        if parts1[0] == parts2[0] and parts1[-1] == parts2[-1]:
            return True
    
    return False

