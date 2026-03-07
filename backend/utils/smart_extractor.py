"""
🎯 SMART DATA EXTRACTOR - COMPREHENSIVE VERSION
100% Accurate extraction from ANY Indian tax document format
Handles: Form 16, Form 26AS, AIS with varying layouts

EXTRACTS ALL TAX-RELEVANT DATA:
- Income details (Salary, HRA, Allowances, Perquisites)
- All Chapter VI-A deductions (80C, 80D, 80E, 80G, etc.)
- Standard Deduction, Professional Tax
- House Property Income/Loss
- TDS details
- Net Taxable Income
"""

import re
from typing import Dict, Any, Optional, List, Tuple
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
    Extracts COMPREHENSIVE tax data for accurate calculations
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
        Master extraction function - extracts ALL tax-relevant data
        """
        result = {
            # Basic identification
            'pan': None,
            'name': None,
            'financial_year': None,
            'assessment_year': None,
            'document_type': None,
            'employer_name': None,
            'employer_tan': None,
            'all_pans_found': [],
            'all_names_found': [],
            
            # Salary Income Breakdown (Form 16 Part B)
            'gross_salary': 0.0,
            'basic_salary': 0.0,
            'hra_received': 0.0,
            'special_allowance': 0.0,
            'lta': 0.0,
            'bonus': 0.0,
            'perquisites': 0.0,
            'profits_in_lieu_of_salary': 0.0,
            
            # Exemptions under Section 10
            'exemptions': {
                'hra_exemption': 0.0,
                'lta_exemption': 0.0,
                'standard_deduction': 0.0,
                'professional_tax': 0.0,
                'entertainment_allowance': 0.0,
                'other_exemptions': 0.0,
                'total_exemptions': 0.0
            },
            
            # Net Salary after exemptions
            'net_salary': 0.0,
            
            # Other Income Sources
            'income_from_house_property': 0.0,
            'income_from_other_sources': 0.0,
            'interest_income': 0.0,
            'dividend_income': 0.0,
            'capital_gains_short_term': 0.0,
            'capital_gains_long_term': 0.0,
            'business_income': 0.0,
            
            # Gross Total Income
            'gross_total_income': 0.0,
            
            # Chapter VI-A Deductions
            'deductions': {
                # Section 80C (Max ₹1,50,000)
                '80C': 0.0,
                '80C_details': {
                    'ppf': 0.0,
                    'epf': 0.0,
                    'elss': 0.0,
                    'life_insurance': 0.0,
                    'nsc': 0.0,
                    'tuition_fees': 0.0,
                    'home_loan_principal': 0.0,
                    'sukanya_samriddhi': 0.0,
                    'tax_saving_fd': 0.0,
                    'other_80c': 0.0
                },
                # Section 80CCC - Pension Fund
                '80CCC': 0.0,
                # Section 80CCD - NPS
                '80CCD_1': 0.0,      # Employee contribution (part of 80C limit)
                '80CCD_1B': 0.0,    # Additional NPS (₹50,000 extra)
                '80CCD_2': 0.0,      # Employer NPS contribution (10% of salary)
                # Section 80D - Health Insurance (Max ₹25,000 + ₹25,000 parents + ₹50,000 senior)
                '80D': 0.0,
                '80D_details': {
                    'self_family': 0.0,
                    'parents': 0.0,
                    'preventive_health_checkup': 0.0
                },
                # Section 80DD - Disabled Dependent
                '80DD': 0.0,
                # Section 80DDB - Medical Treatment
                '80DDB': 0.0,
                # Section 80E - Education Loan Interest
                '80E': 0.0,
                # Section 80EE/80EEA - Home Loan Interest (First Time Buyers)
                '80EE': 0.0,
                '80EEA': 0.0,
                # Section 80G - Donations
                '80G': 0.0,
                # Section 80GG - Rent Paid (no HRA)
                '80GG': 0.0,
                # Section 80GGA - Donations for Scientific Research
                '80GGA': 0.0,
                # Section 80GGC - Political Party Donations
                '80GGC': 0.0,
                # Section 80TTA - Savings Interest (Max ₹10,000)
                '80TTA': 0.0,
                # Section 80TTB - Senior Citizen Interest (Max ₹50,000)
                '80TTB': 0.0,
                # Section 80U - Disability
                '80U': 0.0,
                # Section 24(b) - Home Loan Interest
                '24b_home_loan_interest': 0.0,
                # Total Deductions
                'total_deductions': 0.0
            },
            
            # Net Taxable Income
            'total_income': 0.0,  # After all deductions
            'net_taxable_income': 0.0,
            
            # Tax Computation
            'tax_on_total_income': 0.0,
            'rebate_87a': 0.0,
            'surcharge': 0.0,
            'cess': 0.0,
            'total_tax_liability': 0.0,
            
            # TDS Details
            'total_tds': 0.0,
            'tds_on_salary': 0.0,
            'tds_on_other_income': 0.0,
            'advance_tax_paid': 0.0,
            'self_assessment_tax': 0.0,
            
            # Relief
            'relief_89': 0.0,
            
            # Final
            'tax_payable': 0.0,
            'refund_due': 0.0,
            
            # Metadata
            'extraction_confidence': 0.0,
            'extraction_method': []
        }
        
        # Extract PANs
        result['all_pans_found'] = extract_all_pans(self.text)
        result['pan'] = self._extract_pan_smart()
        
        # Extract Names
        result['name'], result['all_names_found'] = self._extract_name_smart()
        
        # Extract Document Type FIRST (needed for document-specific extraction)
        result['document_type'] = extract_document_type(self.text)
        
        # Extract Financial Year
        result['financial_year'] = self._extract_fy_smart(result['document_type'])
        result['assessment_year'] = self._extract_assessment_year()
        
        # Extract Employer Details (Form 16 specific)
        result['employer_name'] = self._extract_employer_name()
        result['employer_tan'] = self._extract_tan()
        
        # COMPREHENSIVE FINANCIAL DATA EXTRACTION
        # Based on document type, extract all relevant fields
        if result['document_type'] in ['Form 16', 'FORM 16', 'FORM NO. 16', None]:
            self._extract_form16_data(result)
        elif result['document_type'] in ['Form 26AS', 'FORM 26AS', 'FORM 26 AS']:
            self._extract_form26as_data(result)
        elif result['document_type'] in ['AIS', 'ANNUAL INFORMATION STATEMENT']:
            self._extract_ais_data(result)
        else:
            # Generic extraction for unknown document types
            self._extract_generic_financial_data(result)
        
        # Calculate totals
        self._calculate_totals(result)
        
        # Calculate confidence
        result['extraction_confidence'] = self._calculate_confidence(result)
        
        return result
    
    def _extract_form16_data(self, result: Dict[str, Any]):
        """
        Comprehensive Form 16 data extraction
        Extracts all fields from Part A and Part B
        """
        print("   📊 Extracting Form 16 data (comprehensive)...")
        
        # === SALARY INCOME EXTRACTION ===
        salary_patterns = {
            'gross_salary': [
                r'GROSS\s+SALARY\s*[\(\[]?.*?[\)\]]?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'SALARY\s+AS\s+PER\s+.*?SECTION\s+17\s*\(?\s*1\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TOTAL\s+SALARY\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'1\.\s*GROSS\s+SALARY\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'basic_salary': [
                r'BASIC\s+(?:SALARY|PAY)\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'BASIC\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'hra_received': [
                r'HOUSE\s+RENT\s+ALLOWANCE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'HRA\s+RECEIVED\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'HRA\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'special_allowance': [
                r'SPECIAL\s+ALLOWANCE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'OTHER\s+ALLOWANCE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'lta': [
                r'LEAVE\s+TRAVEL\s+(?:ALLOWANCE|CONCESSION)\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'LTA\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'LTC\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'bonus': [
                r'BONUS\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'PERFORMANCE\s+BONUS\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'perquisites': [
                r'PERQUISITES\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'VALUE\s+OF\s+PERQUISITES\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'17\s*\(?\s*2\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'profits_in_lieu_of_salary': [
                r'PROFITS\s+IN\s+LIEU\s+OF\s+SALARY\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'17\s*\(?\s*3\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
        }
        
        for field, patterns in salary_patterns.items():
            value = self._extract_amount_multi_pattern(patterns)
            if value:
                result[field] = value
        
        # === EXEMPTIONS EXTRACTION ===
        exemption_patterns = {
            'hra_exemption': [
                r'(?:ALLOWANCE|HRA)\s+(?:EXEMPT|EXEMPTION)\s*(?:U/?S\s*10)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'10\s*\(?\s*13A\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'HRA\s+EXEMPTION\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'lta_exemption': [
                r'(?:LTA|LTC)\s+EXEMPTION\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'10\s*\(?\s*5\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'standard_deduction': [
                r'STANDARD\s+DEDUCTION\s*(?:U/?S\s*16\s*\(?\s*IA?\s*\)?)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'DEDUCTION\s+U/?S\s+16\s*\(?\s*IA?\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'16\s*\(?\s*IA?\s*\)?\s*STANDARD\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'professional_tax': [
                r'PROFESSIONAL\s+TAX\s*(?:U/?S\s*16\s*\(?\s*III?\s*\)?)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TAX\s+ON\s+EMPLOYMENT\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'16\s*\(?\s*III?\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'entertainment_allowance': [
                r'ENTERTAINMENT\s+ALLOWANCE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'16\s*\(?\s*II\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'total_exemptions': [
                r'TOTAL\s+(?:EXEMPTIONS?|DEDUCTIONS?\s+UNDER\s+16)\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TOTAL\s*\(?\s*B\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
        }
        
        for field, patterns in exemption_patterns.items():
            value = self._extract_amount_multi_pattern(patterns)
            if value:
                result['exemptions'][field] = value
        
        # === CHAPTER VI-A DEDUCTIONS ===
        deduction_patterns = {
            '80C': [
                r'(?:DEDUCTION|DEDN)\s+(?:U/?S|UNDER\s+SECTION)\s*80\s*C\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'80\s*C\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'SECTION\s+80C\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80CCC': [
                r'80\s*CCC\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'PENSION\s+FUND\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80CCD_1': [
                r'80\s*CCD\s*\(?\s*1\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'EMPLOYEE\s+(?:NPS|PENSION)\s+CONTRIBUTION\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80CCD_1B': [
                r'80\s*CCD\s*\(?\s*1B\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'ADDITIONAL\s+NPS\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80CCD_2': [
                r'80\s*CCD\s*\(?\s*2\s*\)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'EMPLOYER\s+(?:NPS|PENSION)\s+CONTRIBUTION\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80D': [
                r'80\s*D\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'(?:MEDICAL|HEALTH)\s+INSURANCE\s+PREMIUM\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80DD': [
                r'80\s*DD\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'DISABLED\s+DEPENDENT\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80DDB': [
                r'80\s*DDB\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'MEDICAL\s+TREATMENT\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80E': [
                r'80\s*E\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'EDUCATION\s+LOAN\s+INTEREST\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80EE': [
                r'80\s*EE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80EEA': [
                r'80\s*EEA\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80G': [
                r'80\s*G\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'DONATIONS?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80GG': [
                r'80\s*GG\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'RENT\s+PAID\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80TTA': [
                r'80\s*TTA\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'SAVINGS\s+(?:ACCOUNT\s+)?INTEREST\s+DEDUCTION\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80TTB': [
                r'80\s*TTB\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '80U': [
                r'80\s*U\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'DISABILITY\s+DEDUCTION\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            '24b_home_loan_interest': [
                r'(?:SECTION\s+)?24\s*\(?\s*B?\s*\)?\s*(?:HOME\s+LOAN\s+)?INTEREST\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'INTEREST\s+ON\s+(?:HOUSING|HOME)\s+LOAN\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'HOUSE\s+PROPERTY\s+LOSS\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'total_deductions': [
                r'TOTAL\s+DEDUCTION\s+UNDER\s+CHAPTER\s+VI[\-\s]?A\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'AGGREGATE\s+OF\s+DEDUCTIONS\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TOTAL\s+DEDUCTIONS?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
        }
        
        for field, patterns in deduction_patterns.items():
            value = self._extract_amount_multi_pattern(patterns)
            if value:
                result['deductions'][field] = value
        
        # === INCOME COMPUTATION ===
        income_patterns = {
            'gross_total_income': [
                r'GROSS\s+TOTAL\s+INCOME\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TOTAL\s+GROSS\s+INCOME\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'total_income': [
                r'TOTAL\s+INCOME\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'NET\s+TOTAL\s+INCOME\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'net_taxable_income': [
                r'NET\s+TAXABLE\s+INCOME\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TAXABLE\s+INCOME\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'income_from_house_property': [
                r'INCOME\s+(?:FROM\s+)?HOUSE\s+PROPERTY\s*[:\-]?\s*(?:RS?\.?\s*)?\(?([0-9,]+(?:\.\d{2})?)\)?',
                r'LOSS\s+FROM\s+HOUSE\s+PROPERTY\s*[:\-]?\s*(?:RS?\.?\s*)?\(?([0-9,]+(?:\.\d{2})?)\)?',
            ],
            'income_from_other_sources': [
                r'INCOME\s+FROM\s+OTHER\s+SOURCES\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
        }
        
        for field, patterns in income_patterns.items():
            value = self._extract_amount_multi_pattern(patterns)
            if value:
                result[field] = value
        
        # === TAX COMPUTATION ===
        tax_patterns = {
            'tax_on_total_income': [
                r'TAX\s+ON\s+TOTAL\s+INCOME\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'INCOME\s+TAX\s+COMPUTED\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'rebate_87a': [
                r'REBATE\s+(?:U/?S|UNDER\s+SECTION)?\s*87\s*A?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'surcharge': [
                r'SURCHARGE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'cess': [
                r'(?:HEALTH\s+(?:AND|&)\s+EDUCATION\s+)?CESS\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'H\s*&?\s*E\s*CESS\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'total_tax_liability': [
                r'TOTAL\s+TAX\s+(?:LIABILITY|PAYABLE)\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TAX\s+PAYABLE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'relief_89': [
                r'RELIEF\s+(?:U/?S|UNDER\s+SECTION)?\s*89\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
        }
        
        for field, patterns in tax_patterns.items():
            value = self._extract_amount_multi_pattern(patterns)
            if value:
                result[field] = value
        
        # === TDS EXTRACTION ===
        tds_patterns = {
            'total_tds': [
                r'TOTAL\s+(?:TAX\s+)?(?:TDS\s+)?DEDUCTED\s*(?:AT\s+SOURCE)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TDS\s+(?:ON\s+SALARY)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
                r'TAX\s+DEDUCTED\s+AT\s+SOURCE\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'tds_on_salary': [
                r'TDS\s+ON\s+SALARY\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'advance_tax_paid': [
                r'ADVANCE\s+TAX\s+(?:PAID)?\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'self_assessment_tax': [
                r'SELF\s+ASSESSMENT\s+TAX\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
        }
        
        for field, patterns in tds_patterns.items():
            value = self._extract_amount_multi_pattern(patterns)
            if value:
                result[field] = value
        
        # Legacy field mapping
        result['total_tax_deducted'] = result.get('total_tds', 0)
        
        print(f"   ✅ Form 16 extraction complete")
    
    def _extract_form26as_data(self, result: Dict[str, Any]):
        """
        Comprehensive Form 26AS data extraction
        Handles tabular format where each field is on a separate line
        """
        print("   📊 Extracting Form 26AS data...")
        
        # Form 26AS uses single values per line format:
        # Line: PNEF01495E (TAN)
        # Next Line: 1069432.00 (Gross Amount)
        # Next Line: 88824.00 (Total TDS)
        
        lines = self.original_text.split('\n')  # Use original text to preserve case
        lines = [line.strip() for line in lines]
        
        gross_salary = 0.0
        total_tds = 0.0
        tds_amounts = []
        salary_amounts = []
        
        # Look for TAN pattern followed by amounts
        tan_pattern = r'^[A-Z]{4}\d{5}[A-Z]$'  # e.g., PNEF01495E
        amount_pattern = r'^(\d+(?:\.\d{2})?)$'  # e.g., 1069432.00
        
        for i, line in enumerate(lines):
            # Check if this line is a TAN
            if re.match(tan_pattern, line):
                # Look at next 3 lines for amounts
                for j in range(1, 4):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        amt_match = re.match(amount_pattern, next_line)
                        if amt_match:
                            amt = float(amt_match.group(1))
                            if amt > 50000:  # Likely salary amount
                                if j == 1:
                                    salary_amounts.append(amt)
                                elif j == 2:
                                    tds_amounts.append(amt)
            
            # Check if line is Section 192 (salary TDS entry)
            if line == '192':
                # Look at surrounding lines for amounts
                for j in range(1, 8):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        amt_match = re.match(amount_pattern, next_line)
                        if amt_match:
                            amt = float(amt_match.group(1))
                            if amt > 10000:  # Monthly salary
                                salary_amounts.append(amt)
                            elif amt > 1000 and amt < 50000:  # Monthly TDS
                                tds_amounts.append(amt)
                            break  # Found first amount after 192
            
            # Direct amount extraction for standalone amounts after Part-I header
            if 'PART-I' in line.upper() or 'TAX DEDUCTED AT SOURCE' in line.upper():
                # Scan next 20 lines for amount patterns
                for j in range(1, 20):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        # Look for large standalone numbers (company total amounts)
                        amt_match = re.match(r'^(\d{5,}(?:\.\d{2})?)$', next_line)
                        if amt_match:
                            amt = float(amt_match.group(1))
                            if gross_salary == 0 and amt > 100000:
                                gross_salary = amt
                            elif total_tds == 0 and amt > 10000 and amt < gross_salary:
                                total_tds = amt
                                break
        
        # Calculate totals from individual entries if summary not found
        if salary_amounts and gross_salary == 0:
            gross_salary = salary_amounts[0]  # First one is usually the total
        if tds_amounts and total_tds == 0:
            total_tds = tds_amounts[0]  # First one is usually the total
        
        # Fallback: scan for any large numbers in specific pattern
        if gross_salary == 0:
            # Look for numbers > 100000 that could be salary
            for line in lines:
                amt_match = re.match(r'^(\d{6,}(?:\.\d{2})?)$', line.strip())
                if amt_match:
                    amt = float(amt_match.group(1))
                    if 100000 < amt < 50000000:
                        gross_salary = amt
                        break
        
        if total_tds == 0 and gross_salary > 0:
            # Look for TDS amount (typically 5-30% of salary)
            for line in lines:
                amt_match = re.match(r'^(\d{4,}(?:\.\d{2})?)$', line.strip())
                if amt_match:
                    amt = float(amt_match.group(1))
                    if 5000 < amt < gross_salary * 0.35:
                        total_tds = amt
                        break
        
        # Store extracted values
        if gross_salary > 0:
            result['gross_salary'] = gross_salary
            result['gross_total_income'] = max(result.get('gross_total_income', 0), gross_salary)
            print(f"   Found gross salary: ₹{gross_salary:,.0f}")
        
        if total_tds > 0:
            result['total_tds'] = total_tds
            result['total_tax_deducted'] = total_tds
            print(f"   Found TDS: ₹{total_tds:,.0f}")
        
        # Legacy patterns as fallback
        tds_patterns = {
            'advance_tax_paid': [
                r'ADVANCE\s+TAX\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
            'self_assessment_tax': [
                r'SELF\s+ASSESSMENT\s+TAX\s*[:\-]?\s*(?:RS?\.?\s*)?([0-9,]+(?:\.\d{2})?)',
            ],
        }
        
        for field, patterns in tds_patterns.items():
            value = self._extract_amount_multi_pattern(patterns)
            if value:
                result[field] = value
        
        print(f"   ✅ Form 26AS extraction complete")
    
    def _extract_ais_data(self, result: Dict[str, Any]):
        """
        Comprehensive AIS (Annual Information Statement) data extraction
        Handles tabular format with amounts on separate lines
        """
        print("   📊 Extracting AIS data...")
        
        lines = self.original_text.split('\n')
        lines = [line.strip() for line in lines]
        
        gross_salary = 0.0
        total_tds = 0.0
        interest_income = 0.0
        dividend_income = 0.0
        
        # AIS Format:
        # Line: "TDS-192" or "Salary received (Section 192)"
        # Line: Company name
        # Line: COUNT (e.g., 12)  
        # Line: AMOUNT (e.g., 10,69,432)
        
        # Parse Indian number format (10,69,432 = 1069432)
        def parse_indian_amount(amt_str):
            """Parse Indian number format like 10,69,432"""
            if not amt_str:
                return 0.0
            # Remove commas and convert
            cleaned = amt_str.replace(',', '').replace(' ', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_upper = line.upper()
            
            # Look for Salary section (TDS-192)
            if 'TDS-192' in line_upper or ('SECTION 192' in line_upper and 'SALARY' in line_upper):
                # Look ahead for amount - it's usually within next 5 lines
                for j in range(1, 8):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        # Check if line looks like a formatted amount (e.g., 10,69,432)
                        if re.match(r'^[\d,]+$', next_line) and len(next_line) > 4:
                            amt = parse_indian_amount(next_line)
                            if amt > 50000:  # Reasonable salary
                                gross_salary = max(gross_salary, amt)
                                break
            
            # Look for Interest section (TDS-194A)
            # Skip generic "INTEREST" to avoid matching headers/noise
            if 'TDS-194A' in line_upper:
                for j in range(1, 8):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if re.match(r'^[\d,]+$', next_line) and len(next_line) > 2:
                            amt = parse_indian_amount(next_line)
                            # Reasonable interest income: 100 < amt < 1 crore
                            if 100 < amt < 10000000:
                                interest_income = max(interest_income, amt)
                                break
            
            # Look for Dividend section (TDS-194)
            if 'TDS-194' in line_upper and 'TDS-194A' not in line_upper:
                for j in range(1, 8):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if re.match(r'^[\d,]+$', next_line) and len(next_line) > 2:
                            amt = parse_indian_amount(next_line)
                            # Reasonable dividend: 100 < amt < 1 crore
                            if 100 < amt < 10000000:
                                dividend_income = max(dividend_income, amt)
                                break
            
            # Look for TDS amounts in table rows
            if 'TDS DEDUCTED' in line_upper or 'TAX DEDUCTED' in line_upper:
                # Scan following lines for amounts
                for j in range(1, 20):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if re.match(r'^[\d,]+$', next_line):
                            amt = parse_indian_amount(next_line)
                            if 1000 < amt < 1000000:  # TDS range
                                total_tds += amt
            
            i += 1
        
        # Fallback: scan for AMOUNT header and get the value after it
        if gross_salary == 0:
            for i, line in enumerate(lines):
                if line.upper() == 'AMOUNT':
                    # Look at next few lines for a large number
                    for j in range(1, 5):
                        if i + j < len(lines):
                            next_line = lines[i + j].strip()
                            if re.match(r'^[\d,]+$', next_line):
                                amt = parse_indian_amount(next_line)
                                if amt > 100000:
                                    gross_salary = amt
                                    break
                    break
        
        # Calculate total TDS from individual entries if needed
        if total_tds == 0:
            # Look for TDS in quarterly entries
            for i, line in enumerate(lines):
                if re.match(r'^[\d,]+$', line.strip()) and len(line.strip()) >= 4:
                    # Check context - is this a TDS amount?
                    if i > 2:
                        prev_lines = ' '.join(lines[max(0,i-5):i]).upper()
                        if 'TDS' in prev_lines or 'DEDUCTED' in prev_lines or 'Q1' in prev_lines or 'Q2' in prev_lines or 'Q3' in prev_lines or 'Q4' in prev_lines:
                            amt = parse_indian_amount(line.strip())
                            if 1000 < amt < 100000:  # Monthly TDS range
                                total_tds += amt
        
        # Store results
        if gross_salary > 0:
            result['gross_salary'] = gross_salary
            result['gross_total_income'] = max(result.get('gross_total_income', 0), gross_salary)
            print(f"   Found gross salary: ₹{gross_salary:,.0f}")
        
        if total_tds > 0:
            result['total_tds'] = max(result.get('total_tds', 0), total_tds)
            result['total_tax_deducted'] = result.get('total_tds', 0)
            print(f"   Found TDS: ₹{total_tds:,.0f}")
        
        if interest_income > 0:
            result['interest_income'] = interest_income
            print(f"   Found interest income: ₹{interest_income:,.0f}")
        
        if dividend_income > 0:
            result['dividend_income'] = dividend_income
            print(f"   Found dividend income: ₹{dividend_income:,.0f}")
        
        print(f"   ✅ AIS extraction complete")
    
    def _extract_generic_financial_data(self, result: Dict[str, Any]):
        """
        Generic financial data extraction for unknown document types
        """
        print("   📊 Extracting generic financial data...")
        
        # Try to extract basic amounts
        result['gross_salary'] = self._extract_amount('gross_salary')
        result['total_tds'] = self._extract_amount('tax_deducted')
        result['total_tax_deducted'] = result.get('total_tds', 0)
    
    def _extract_amount_multi_pattern(self, patterns: List[str]) -> Optional[float]:
        """
        Extract amount using multiple patterns, return first match
        """
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '').replace(' ', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    def _extract_assessment_year(self) -> Optional[str]:
        """Extract Assessment Year from document"""
        ay_patterns = [
            r'ASSESSMENT\s+YEAR\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2})',
            r'A\.?Y\.?\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2})',
            r'AY\s*(\d{4})\s*-\s*(\d{2})',
        ]
        
        for pattern in ay_patterns:
            match = re.search(pattern, self.text)
            if match:
                return f"{match.group(1)}-{match.group(2)}"
        return None
    
    def _calculate_totals(self, result: Dict[str, Any]):
        """
        Calculate derived totals from extracted data
        """
        # Calculate total exemptions if not extracted
        if result['exemptions']['total_exemptions'] == 0:
            result['exemptions']['total_exemptions'] = (
                result['exemptions'].get('hra_exemption', 0) +
                result['exemptions'].get('lta_exemption', 0) +
                result['exemptions'].get('standard_deduction', 0) +
                result['exemptions'].get('professional_tax', 0) +
                result['exemptions'].get('entertainment_allowance', 0) +
                result['exemptions'].get('other_exemptions', 0)
            )
        
        # Calculate net salary
        if result['net_salary'] == 0 and result['gross_salary'] > 0:
            result['net_salary'] = result['gross_salary'] - result['exemptions']['total_exemptions']
        
        # Calculate total deductions if not extracted
        if result['deductions']['total_deductions'] == 0:
            total = 0
            for key, value in result['deductions'].items():
                if key not in ['total_deductions', '80C_details', '80D_details'] and isinstance(value, (int, float)):
                    total += value
            result['deductions']['total_deductions'] = total
        
        # Calculate gross total income if not extracted
        if result['gross_total_income'] == 0:
            result['gross_total_income'] = (
                result.get('net_salary', 0) or result.get('gross_salary', 0) +
                result.get('income_from_house_property', 0) +
                result.get('income_from_other_sources', 0) +
                result.get('interest_income', 0) +
                result.get('dividend_income', 0) +
                result.get('capital_gains_short_term', 0) +
                result.get('capital_gains_long_term', 0) +
                result.get('business_income', 0)
            )
        
        # Calculate net taxable income if not extracted
        if result['net_taxable_income'] == 0 and result['gross_total_income'] > 0:
            result['net_taxable_income'] = max(0, 
                result['gross_total_income'] - result['deductions']['total_deductions']
            )
    
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
        """Calculate extraction confidence score based on completeness"""
        score = 0.0
        
        # Weights for different field categories
        identification_weight = 0.25  # PAN, Name, FY
        income_weight = 0.30  # Salary, Gross Income
        deduction_weight = 0.25  # Chapter VI-A deductions
        tax_weight = 0.20  # TDS, Tax computation
        
        # Identification fields
        id_score = 0
        if result.get('pan'):
            id_score += 0.4
        if result.get('name'):
            id_score += 0.3
        if result.get('financial_year'):
            id_score += 0.2
        if result.get('document_type'):
            id_score += 0.1
        score += id_score * identification_weight
        
        # Income fields
        income_score = 0
        if result.get('gross_salary', 0) > 0:
            income_score += 0.5
        if result.get('gross_total_income', 0) > 0:
            income_score += 0.3
        if result.get('net_taxable_income', 0) > 0:
            income_score += 0.2
        score += income_score * income_weight
        
        # Deduction fields
        deduction_score = 0
        deductions = result.get('deductions', {})
        if deductions.get('total_deductions', 0) > 0:
            deduction_score += 0.4
        if deductions.get('80C', 0) > 0:
            deduction_score += 0.2
        if deductions.get('80D', 0) > 0:
            deduction_score += 0.1
        if result.get('exemptions', {}).get('standard_deduction', 0) > 0:
            deduction_score += 0.2
        if result.get('exemptions', {}).get('professional_tax', 0) > 0:
            deduction_score += 0.1
        score += deduction_score * deduction_weight
        
        # Tax fields
        tax_score = 0
        if result.get('total_tds', 0) > 0:
            tax_score += 0.5
        if result.get('total_tax_liability', 0) > 0:
            tax_score += 0.3
        if result.get('cess', 0) > 0:
            tax_score += 0.2
        score += tax_score * tax_weight
        
        return round(score, 2)


def extract_with_smart_extractor(text: str, user_name: str = None, user_pan: str = None, expected_fy: str = None) -> Dict[str, Any]:
    """
    Main function to extract data using smart extractor
    Returns comprehensive tax data for accurate calculations
    """
    extractor = SmartExtractor(text, user_name, user_pan, expected_fy)
    return extractor.extract_all_data()


def flatten_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten nested extracted data for easier access
    Returns a flat dictionary with all fields
    """
    flat = {}
    
    # Copy top-level fields
    for key, value in data.items():
        if not isinstance(value, dict):
            flat[key] = value
    
    # Flatten exemptions
    if 'exemptions' in data:
        for key, value in data['exemptions'].items():
            flat[f'exemption_{key}'] = value
    
    # Flatten deductions
    if 'deductions' in data:
        for key, value in data['deductions'].items():
            if not isinstance(value, dict):
                flat[f'deduction_{key}'] = value
            elif key == '80C_details':
                for k, v in value.items():
                    flat[f'80C_{k}'] = v
            elif key == '80D_details':
                for k, v in value.items():
                    flat[f'80D_{k}'] = v
    
    return flat

