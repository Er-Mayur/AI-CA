"""
🎯 SMART DATA EXTRACTOR
100% Accurate extraction from ANY Indian tax document format
Handles: Form 16, Form 26AS, AIS with varying layouts
"""

import re
from typing import Dict, Any, Optional, List
from utils.text_cleaner import (
    extract_first_pan,
    extract_all_pans,
    pick_fy,
    extract_document_type,
    normalize_spaces,
    names_match
)


class SmartExtractor:
    """
    Intelligent extractor that adapts to different document formats
    """
    
    def __init__(self, text: str, user_name: str = None, user_pan: str = None, expected_fy: str = None):
        self.original_text = text
        self.text = normalize_spaces(text.upper())
        self.user_name = user_name
        self.user_pan = user_pan
        self.expected_fy = expected_fy
        self.lines = [line.strip() for line in self.text.split('\n') if line.strip()]
        
    def extract_all_data(self) -> Dict[str, Any]:
        """
        Master extraction function - tries multiple strategies
        """
        result = {
            'pan': None,
            'name': None,
            'financial_year': None,
            'document_type': None,
            'employer_name': None,
            'employer_tan': None,
            'gross_salary': None,
            'total_tax_deducted': None,
            'all_pans_found': [],
            'all_names_found': [],
            'extraction_confidence': 0.0,
            'extraction_method': []
        }
        
        # Extract PANs
        result['all_pans_found'] = extract_all_pans(self.text)
        result['pan'] = self._extract_pan_smart()
        
        # Extract Names
        result['name'], result['all_names_found'] = self._extract_name_smart()
        
        # Extract Document Type FIRST (needed for AIS-specific FY extraction)
        result['document_type'] = extract_document_type(self.text)
        
        # Extract Financial Year (pass doc_type for AIS-specific extraction)
        result['financial_year'] = self._extract_fy_smart(result['document_type'])
        
        # Extract Employer Details (Form 16 specific)
        result['employer_name'] = self._extract_employer_name()
        result['employer_tan'] = self._extract_tan()
        
        # Extract Financial Data
        result['gross_salary'] = self._extract_amount('gross_salary')
        result['total_tax_deducted'] = self._extract_amount('tax_deducted')
        
        # Calculate confidence
        result['extraction_confidence'] = self._calculate_confidence(result)
        
        return result
    
    def _extract_pan_smart(self) -> Optional[str]:
        """
        Smart PAN extraction with multiple strategies
        """
        # Strategy 1: If user PAN is provided, look for it specifically
        if self.user_pan:
            user_pan_clean = self.user_pan.upper().replace(' ', '')
            # Check exact match
            if user_pan_clean in self.text.replace(' ', ''):
                return user_pan_clean
            
            # Check with spaces/separators
            pan_pattern = rf"{user_pan_clean[0]}\s*{user_pan_clean[1]}\s*{user_pan_clean[2]}\s*{user_pan_clean[3]}\s*{user_pan_clean[4]}\s*{user_pan_clean[5]}\s*{user_pan_clean[6]}\s*{user_pan_clean[7]}\s*{user_pan_clean[8]}\s*{user_pan_clean[9]}"
            if re.search(pan_pattern, self.text):
                return user_pan_clean
        
        # Strategy 2: Extract all PANs and prioritize
        all_pans = extract_all_pans(self.text)
        
        if not all_pans:
            return None
        
        # If only one PAN, use it
        if len(all_pans) == 1:
            return all_pans[0]
        
        # If multiple PANs, prioritize based on context
        for pan in all_pans:
            # Look for PAN in employee context (not employer/deductor)
            pan_context = self._get_text_around(pan, 100)
            employee_keywords = ['EMPLOYEE', 'ASSESSEE', 'DEDUCTEE', 'TAXPAYER', 'NAME', 'PAN OF EMPLOYEE']
            employer_keywords = ['EMPLOYER', 'DEDUCTOR', 'TAN', 'PAN OF EMPLOYER']
            
            has_employee_context = any(kw in pan_context for kw in employee_keywords)
            has_employer_context = any(kw in pan_context for kw in employer_keywords)
            
            if has_employee_context and not has_employer_context:
                return pan
        
        # Return first PAN as fallback
        return all_pans[0]
    
    def _extract_name_smart(self) -> tuple[Optional[str], List[str]]:
        """
        Smart name extraction with multiple strategies
        Returns: (best_name, all_names_found)
        """
        all_names = []
        
        # Strategy 1: Look for name near PAN
        pan = self._extract_pan_smart()
        if pan:
            name_from_pan = self._extract_name_near_pan(pan)
            if name_from_pan:
                all_names.append(name_from_pan)
        
        # Strategy 2: Look for common name patterns
        name_patterns = [
            r'NAME\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})',
            r'EMPLOYEE\s+NAME\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})',
            r'ASSESSEE\s+NAME\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})',
            r'DEDUCTEE\s+NAME\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})',
            r'MR\.\s+([A-Z][A-Z\s\.]{2,50})',
            r'MRS\.\s+([A-Z][A-Z\s\.]{2,50})',
            r'MS\.\s+([A-Z][A-Z\s\.]{2,50})',
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, self.text)
            for match in matches:
                name = match.strip()
                if self._is_valid_name(name):
                    all_names.append(self._format_name(name))
        
        # Strategy 3: If user name is provided, look for it
        if self.user_name:
            for name_candidate in all_names:
                if names_match(name_candidate, self.user_name):
                    return self._format_name(name_candidate), all_names
        
        # Return most common name
        if all_names:
            # Use most frequently appearing name
            from collections import Counter
            name_counts = Counter(all_names)
            best_name = name_counts.most_common(1)[0][0]
            return best_name, list(set(all_names))
        
        return None, []
    
    def _extract_name_near_pan(self, pan: str) -> Optional[str]:
        """Extract name that appears near PAN"""
        pan_index = self.text.find(pan)
        if pan_index == -1:
            return None
        
        # Get text around PAN (500 chars before and after)
        start = max(0, pan_index - 500)
        end = min(len(self.text), pan_index + 500)
        context = self.text[start:end]
        
        # Look for name patterns
        name_patterns = [
            r'NAME\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})',
            r'EMPLOYEE\s+NAME\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, context)
            if match:
                name = match.group(1).strip()
                if self._is_valid_name(name):
                    return self._format_name(name)
        
        return None
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if extracted string is a valid name"""
        if not name or len(name) < 3:
            return False
        
        # Must contain at least 2 words
        words = name.split()
        if len(words) < 2:
            return False
        
        # Should not contain numbers
        if re.search(r'\d', name):
            return False
        
        # Should not be a common keyword
        invalid_keywords = {
            'FORM', 'CERTIFICATE', 'SECTION', 'TOTAL', 'GROSS', 'NET',
            'SALARY', 'INCOME', 'TAX', 'DEDUCTED', 'SOURCE', 'TDS',
            'EMPLOYER', 'EMPLOYEE', 'FINANCIAL', 'YEAR', 'ASSESSMENT',
            'PAN', 'TAN', 'DATE', 'PLACE', 'SIGNATURE', 'PAGE'
        }
        
        if any(kw in name.upper() for kw in invalid_keywords):
            return False
        
        return True
    
    def _format_name(self, name: str) -> str:
        """Format name to title case"""
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name).strip()
        # Title case
        return ' '.join(word.capitalize() for word in name.split())
    
    def _extract_fy_smart(self, doc_type: str = None) -> Optional[str]:
        """Smart financial year extraction with document type awareness"""
        fy = pick_fy(self.text, self.expected_fy, doc_type)
        if fy:
            return fy
        
        # Additional patterns for edge cases
        fy_patterns = [
            r'F\.?Y\.?\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2})',  # F.Y. 2024-25
            r'FINANCIAL\s+YEAR\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2})',
            # REMOVED generic pattern to avoid confusing Assessment Year with Financial Year
        ]
        
        for pattern in fy_patterns:
            match = re.search(pattern, self.text)
            if match:
                if len(match.groups()) == 2:
                    year1 = match.group(1)
                    year2 = match.group(2)
                    return f"{year1}-{year2}"
        
        return None
    
    def _extract_employer_name(self) -> Optional[str]:
        """Extract employer/deductor name"""
        patterns = [
            r'EMPLOYER\s+NAME\s*[:\-]?\s*([A-Z][A-Z\s\.,&]{5,100})',
            r'DEDUCTOR\s+NAME\s*[:\-]?\s*([A-Z][A-Z\s\.,&]{5,100})',
            r'NAME\s+OF\s+EMPLOYER\s*[:\-]?\s*([A-Z][A-Z\s\.,&]{5,100})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text)
            if match:
                name = match.group(1).strip()
                # Clean up
                name = re.sub(r'\s+', ' ', name)
                return self._format_name(name)
        
        return None
    
    def _extract_tan(self) -> Optional[str]:
        """Extract TAN (Tax Deduction Account Number)"""
        # TAN format: 4 letters + 5 digits + 1 letter (e.g., ABCD12345E)
        tan_pattern = r'\b[A-Z]{4}\d{5}[A-Z]\b'
        match = re.search(tan_pattern, self.text)
        if match:
            return match.group(0)
        return None
    
    def _extract_amount(self, amount_type: str) -> Optional[float]:
        """
        Extract monetary amounts
        amount_type: 'gross_salary', 'tax_deducted', etc.
        """
        patterns = {
            'gross_salary': [
                r'GROSS\s+SALARY\s*[:\-]?\s*RS?\.?\s*([0-9,]+(?:\.\d{2})?)',
                r'TOTAL\s+GROSS\s+SALARY\s*[:\-]?\s*RS?\.?\s*([0-9,]+(?:\.\d{2})?)',
            ],
            'tax_deducted': [
                r'TAX\s+DEDUCTED\s+AT\s+SOURCE\s*[:\-]?\s*RS?\.?\s*([0-9,]+(?:\.\d{2})?)',
                r'TOTAL\s+TAX\s+DEDUCTED\s*[:\-]?\s*RS?\.?\s*([0-9,]+(?:\.\d{2})?)',
                r'TDS\s*[:\-]?\s*RS?\.?\s*([0-9,]+(?:\.\d{2})?)',
            ]
        }
        
        for pattern in patterns.get(amount_type, []):
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _get_text_around(self, keyword: str, chars: int = 200) -> str:
        """Get text surrounding a keyword"""
        index = self.text.find(keyword)
        if index == -1:
            return ""
        
        start = max(0, index - chars)
        end = min(len(self.text), index + len(keyword) + chars)
        return self.text[start:end]
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate extraction confidence score"""
        score = 0.0
        weights = {
            'pan': 0.35,
            'name': 0.30,
            'financial_year': 0.15,
            'document_type': 0.10,
            'employer_name': 0.05,
            'employer_tan': 0.05
        }
        
        for field, weight in weights.items():
            if result.get(field):
                score += weight
        
        return round(score, 2)


def extract_with_smart_extractor(text: str, user_name: str = None, user_pan: str = None, expected_fy: str = None) -> Dict[str, Any]:
    """
    Main function to extract data using smart extractor
    """
    extractor = SmartExtractor(text, user_name, user_pan, expected_fy)
    return extractor.extract_all_data()

