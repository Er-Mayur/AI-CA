"""
ITR-1 (SAHAJ) PDF Report Generator

Generates a comprehensive PDF report containing all data fields required to fill
the official ITR-1 form on the Income Tax portal.

ITR-1 is for Resident Individuals with:
- Income from Salary/Pension
- Income from One House Property
- Income from Other Sources (Interest, Dividend, etc.)
- Total Income up to Rs.50 Lakhs
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional

# Indian State Codes for ITR-1
STATE_CODES = {
    "01": "Andaman and Nicobar Islands", "02": "Andhra Pradesh", "03": "Arunachal Pradesh",
    "04": "Assam", "05": "Bihar", "06": "Chandigarh", "07": "Dadra Nagar and Haveli",
    "08": "Daman and Diu", "09": "Delhi", "10": "Goa", "11": "Gujarat", "12": "Haryana",
    "13": "Himachal Pradesh", "14": "Jammu and Kashmir", "15": "Karnataka", "16": "Kerala",
    "17": "Lakshadweep", "18": "Madhya Pradesh", "19": "Maharashtra", "20": "Manipur",
    "21": "Meghalaya", "22": "Mizoram", "23": "Nagaland", "24": "Odisha", "25": "Puducherry",
    "26": "Punjab", "27": "Rajasthan", "28": "Sikkim", "29": "Tamil Nadu", "30": "Tripura",
    "31": "Uttar Pradesh", "32": "West Bengal", "33": "Chhattisgarh", "34": "Uttarakhand",
    "35": "Jharkhand", "36": "Telangana", "37": "Ladakh"
}

EMPLOYER_CATEGORIES = {
    "CGOV": "Central Government",
    "SGOV": "State Government",
    "PSU": "Public Sector Unit",
    "PE": "Pensioners - Central Government",
    "PESG": "Pensioners - State Government",
    "PEPS": "Pensioners - Public Sector",
    "PEO": "Pensioners - Others",
    "OTH": "Others",
    "NA": "Not Applicable"
}


def format_currency(amount: float) -> str:
    """Format amount in Indian currency format"""
    if amount is None:
        return "Rs.0"
    amount = abs(int(amount))
    if amount == 0:
        return "Rs.0"
    s = str(amount)
    if len(s) <= 3:
        return f"Rs.{s}"
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return f"Rs.{result.lstrip(',')}"


def format_date(date_obj) -> str:
    """Format date as YYYY-MM-DD"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d")
    elif isinstance(date_obj, str):
        return date_obj
    return ""


class ITR1PDFGenerator:
    """Generate Helper PDF Report"""
    
    def __init__(self, tax_rules: Optional[Dict[str, Any]] = None):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.tax_rules = tax_rules or {}
        
        # Set defaults from tax_rules or fallback values
        self._init_rule_values()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#1e40af'),
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading3'],
            fontSize=11,
            spaceAfter=6,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6b7280')
        ))
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='Instructions',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9ca3af'),
            fontStyle='italic'
        ))
    
    def _init_rule_values(self):
        """Initialize rule values from tax_rules dict"""
        # Standard deduction and salary deductions
        self.standard_deduction = self.tax_rules.get('Standard Deduction', 75000)
        self.professional_tax_limit = self.tax_rules.get('Professional Tax', 2500)
        self.entertainment_allowance_limit = 5000  # Constitutional limit for govt employees
        
        # Section 80C family
        self.sec_80c_limit = self.tax_rules.get('80C', 150000)
        self.sec_80ccd1b_limit = self.tax_rules.get('80CCD_1B', 50000)
        self.sec_80ccd2_percent = self.tax_rules.get('80CCD_2_percent', 10)
        
        # Section 80D
        self.sec_80d_self = self.tax_rules.get('80D_self', 25000)
        self.sec_80d_parents = self.tax_rules.get('80D_parents', 25000)
        self.sec_80d_parents_senior = self.tax_rules.get('80D_parents_senior', 50000)
        self.sec_80d_max = 100000  # Combined max
        
        # Disability
        self.sec_80dd = self.tax_rules.get('80DD', 75000)
        self.sec_80dd_severe = self.tax_rules.get('80DD_severe', 125000)
        self.sec_80ddb = self.tax_rules.get('80DDB', 40000)
        self.sec_80u = self.tax_rules.get('80U', 75000)
        self.sec_80u_severe = self.tax_rules.get('80U_severe', 125000)
        
        # Interest and loans
        self.sec_80tta = self.tax_rules.get('80TTA', 10000)
        self.sec_80ttb = self.tax_rules.get('80TTB', 50000)
        self.sec_80ee = self.tax_rules.get('80EE', 50000)
        self.sec_80eea = self.tax_rules.get('80EEA', 150000)
        self.sec_24b_limit = self.tax_rules.get('24b', 200000)
        
        # Rent
        self.sec_80gg_limit = self.tax_rules.get('80GG', 60000)
        
        # Rebate 87A
        rebate_new = self.tax_rules.get('rebate_87a_new', {})
        rebate_old = self.tax_rules.get('rebate_87a_old', {})
        self.rebate_new_max = rebate_new.get('max_rebate', 25000)
        self.rebate_old_max = rebate_old.get('max_rebate', 12500)
        
        # Cess
        self.cess_percent = self.tax_rules.get('cess_percent', 4)
    
    def _calculate_filing_due_date(self, financial_year: str) -> str:
        """Calculate filing due date based on financial year"""
        # Format: FY 2024-25 -> Due date July 31, 2025
        try:
            fy_parts = financial_year.split("-")
            if len(fy_parts) == 2:
                # Get the end year (e.g., 25 from 2024-25)
                end_year = int(fy_parts[1])
                # Filing due date is July 31 of the next calendar year
                full_year = 2000 + end_year if end_year < 100 else end_year
                return f"{full_year}-07-31"
        except (ValueError, IndexError):
            pass
        return "Check portal"
    
    def _calculate_assessment_year(self, financial_year: str) -> str:
        """Calculate assessment year from financial year"""
        # Format: FY 2024-25 -> AY 2025-26
        try:
            fy_parts = financial_year.split("-")
            if len(fy_parts) == 2:
                start_year = int(fy_parts[0]) if len(fy_parts[0]) == 4 else 2000 + int(fy_parts[0])
                end_year_short = int(fy_parts[1])
                # AY starts from the next year
                return f"{start_year + 1}-{(end_year_short + 1) % 100:02d}"
        except (ValueError, IndexError):
            pass
        return ""
    
    def generate_pdf(
        self,
        user_data: Dict[str, Any],
        computation: Dict[str, Any],
        documents_data: Dict[str, Any],
        financial_year: str
    ) -> BytesIO:
        """
        Generate Helper PDF
        
        Args:
            user_data: User personal information
            computation: Tax computation result
            documents_data: Aggregated data from documents
            financial_year: FY like "2024-25"
        
        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        story = []
        
        # Title and Header
        story.extend(self._create_header(financial_year, computation))
        
        # Personal Information Section
        story.extend(self._create_personal_info_section(user_data))
        
        # Income Details Section
        story.extend(self._create_income_section(computation, documents_data))
        
        # Deductions Section (Chapter VI-A)
        story.extend(self._create_deductions_section(computation, documents_data))
        
        # Tax Computation Section
        story.extend(self._create_tax_computation_section(computation))
        
        # TDS Details Section
        story.extend(self._create_tds_section(computation, documents_data))
        
        # Tax Payable/Refund Section
        story.extend(self._create_final_tax_section(computation))
        
        # Instructions Section
        story.extend(self._create_instructions_section(computation))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _create_header(self, financial_year: str, computation: Dict) -> list:
        """Create PDF header with title and key info"""
        story = []
        
        # Assessment Year - use computation value or calculate dynamically
        assessment_year = computation.get("assessment_year") or self._calculate_assessment_year(financial_year)
        
        # Filing due date - calculate dynamically
        filing_due_date = self._calculate_filing_due_date(financial_year)
        
        # Title Table
        title_data = [
            [Paragraph("<b>Income Tax Return Helper Report</b>", self.styles['Title'])],
            [Paragraph(f"For Assessment Year: {assessment_year}", self.styles['Normal'])],
        ]
        title_table = Table(title_data, colWidths=[180*mm])
        title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(title_table)
        story.append(Spacer(1, 5*mm))
        
        # Info Box
        regime = computation.get("recommended_regime", "New Regime")
        opt_out = "Y" if regime == "Old Regime" else "N"
        
        info_data = [
            ["Financial Year", financial_year, "Assessment Year", assessment_year],
            ["Recommended Regime", regime, "OptOutNewTaxRegime", opt_out],
            ["Recommended ITR Form", computation.get("recommended_itr_form", "ITR-1"), "Filing Due Date", filing_due_date],
        ]
        info_table = Table(info_data, colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def _create_personal_info_section(self, user_data: Dict) -> list:
        """Create Personal Information section (Part A)"""
        story = []
        story.append(Paragraph("PART A: PERSONAL INFORMATION", self.styles['SectionHeader']))
        
        # Parse name
        full_name = user_data.get("name", "")
        name_parts = full_name.split() if full_name else []
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
        surname = name_parts[-1] if len(name_parts) > 1 else ""
        
        # DOB
        dob = user_data.get("date_of_birth", "")
        if isinstance(dob, datetime):
            dob_str = dob.strftime("%Y-%m-%d")
        else:
            dob_str = str(dob) if dob else ""
        
        personal_data = [
            ["ITR-1 Field", "Value", "Portal Reference"],
            ["PAN", user_data.get("pan_card", ""), "PersonalInfo > PAN"],
            ["First Name", first_name, "AssesseeName > FirstName"],
            ["Middle Name", middle_name, "AssesseeName > MiddleName"],
            ["Surname", surname, "AssesseeName > SurNameOrOrgName"],
            ["Date of Birth (YYYY-MM-DD)", dob_str, "PersonalInfo > DOB"],
            ["Mobile Number", user_data.get("mobile", ""), "Address > MobileNo"],
            ["Email", user_data.get("email", ""), "Address > EmailAddress"],
            ["Employer Category", "OTH - Others", "EmployerCategory"],
        ]
        
        table = Table(personal_data, colWidths=[60*mm, 70*mm, 50*mm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f3f4f6')),
        ]))
        story.append(table)
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def _create_income_section(self, computation: Dict, documents_data: Dict) -> list:
        """Create Income Details section (Part B)"""
        story = []
        story.append(Paragraph("PART B: COMPUTATION OF INCOME", self.styles['SectionHeader']))
        
        # === B1: SALARY INCOME ===
        story.append(Paragraph("B1. Income from Salary", self.styles['SubHeader']))
        
        gross_salary = computation.get("salary_income", 0)
        exemptions = documents_data.get("exemptions", {})
        standard_deduction = exemptions.get("standard_deduction", self.standard_deduction)
        professional_tax = exemptions.get("professional_tax", 0)
        
        # Get deduction values based on regime
        regime = computation.get("recommended_regime", "New Regime")
        deductions = computation.get("old_regime_deductions", {}) if regime == "Old Regime" else computation.get("new_regime_deductions", {})
        
        salary_data = [
            ["ITR-1 Field", "Amount", "Portal Reference"],
            ["Gross Salary (17(1))", format_currency(gross_salary), "GrossSalary"],
            ["Salary as per Section 17(1)", format_currency(gross_salary), "Salary"],
            ["Value of Perquisites (17(2))", format_currency(0), "PerquisitesValue"],
            ["Profits in lieu of Salary (17(3))", format_currency(0), "ProfitsInSalary"],
            ["Allowances Exempt u/s 10", format_currency(exemptions.get("total_exemptions", 0)), "AllwncExemptUs10 > TotalAllwncExemptUs10"],
            ["Net Salary (1-2)", format_currency(gross_salary - exemptions.get("total_exemptions", 0)), "NetSalary"],
            ["Standard Deduction u/s 16(ia)", format_currency(min(standard_deduction, self.standard_deduction)), f"DeductionUs16ia (max {format_currency(self.standard_deduction)})"],
            ["Entertainment Allowance u/s 16(ii)", format_currency(0), f"EntertainmentAlw16ii (max {format_currency(self.entertainment_allowance_limit)})"],
            ["Professional Tax u/s 16(iii)", format_currency(min(professional_tax, self.professional_tax_limit)), f"ProfessionalTaxUs16iii (max {format_currency(self.professional_tax_limit)})"],
            ["Income from Salary", format_currency(computation.get("salary_income", 0) - min(standard_deduction, self.standard_deduction) - min(professional_tax, self.professional_tax_limit)), "IncomeFromSal"],
        ]
        
        table = Table(salary_data, colWidths=[75*mm, 45*mm, 60*mm])
        table.setStyle(self._get_table_style())
        story.append(table)
        story.append(Spacer(1, 5*mm))
        
        # === B2: HOUSE PROPERTY INCOME ===
        story.append(Paragraph("B2. Income from House Property", self.styles['SubHeader']))
        
        hp_income = computation.get("house_property_income", 0)
        hp_type = "S" if hp_income <= 0 else "L"  # S=Self Occupied, L=Let Out
        
        hp_data = [
            ["ITR-1 Field", "Amount", "Portal Reference"],
            ["Type of House Property", hp_type + " (S=Self Occupied, L=Let Out)", "TypeOfHP"],
            ["Gross Rent Received", format_currency(max(0, hp_income)), "GrossRentReceived"],
            ["Tax Paid to Local Authority", format_currency(0), "TaxPaidlocalAuth"],
            ["Annual Value", format_currency(max(0, hp_income)), "AnnualValue"],
            ["30% Standard Deduction", format_currency(int(max(0, hp_income) * 0.3)), "StandardDeduction"],
            ["Interest on Housing Loan u/s 24(b)", format_currency(deductions.get("24b_home_loan_interest", 0) if isinstance(deductions, dict) else 0), f"InterestPayable (max {format_currency(self.sec_24b_limit)} for SOP)"],
            ["Total Income from HP", format_currency(hp_income), f"TotalIncomeOfHP (can be negative up to -{format_currency(self.sec_24b_limit)})"],
        ]
        
        table = Table(hp_data, colWidths=[75*mm, 45*mm, 60*mm])
        table.setStyle(self._get_table_style())
        story.append(table)
        story.append(Spacer(1, 5*mm))
        
        # === B3: OTHER SOURCES ===
        story.append(Paragraph("B3. Income from Other Sources", self.styles['SubHeader']))
        
        other_income = computation.get("other_income", 0)
        interest_income = documents_data.get("interest_income", 0)
        dividend_income = documents_data.get("dividend_income", 0)
        
        other_data = [
            ["ITR-1 Field", "Amount", "Portal Reference"],
            ["Interest from Savings Account (SAV)", format_currency(interest_income), "OthersInc > OthSrcNatureDesc='SAV'"],
            ["Interest from Deposits (IFD)", format_currency(0), "OthersInc > OthSrcNatureDesc='IFD'"],
            ["Dividend Income (DIV)", format_currency(dividend_income), "OthersInc > OthSrcNatureDesc='DIV'"],
            ["Family Pension (FAP)", format_currency(0), "OthersInc > OthSrcNatureDesc='FAP'"],
            ["Any Other Income", format_currency(max(0, other_income - interest_income - dividend_income)), "OthersInc > OthSrcNatureDesc='OTH'"],
            ["Deduction u/s 57(iia)", format_currency(0), "DeductionUs57iia (family pension, max Rs.25,000)"],
            ["Total Other Income", format_currency(other_income), "IncomeOthSrc"],
        ]
        
        table = Table(other_data, colWidths=[75*mm, 45*mm, 60*mm])
        table.setStyle(self._get_table_style())
        story.append(table)
        story.append(Spacer(1, 5*mm))
        
        # === GROSS TOTAL INCOME ===
        story.append(Paragraph("B4. Gross Total Income", self.styles['SubHeader']))
        
        gti_data = [
            ["ITR-1 Field", "Amount", "Portal Reference"],
            ["Income from Salary (B1)", format_currency(computation.get("salary_income", 0) - min(standard_deduction, 75000)), "IncomeFromSal"],
            ["Income from House Property (B2)", format_currency(hp_income), "TotalIncomeOfHP"],
            ["Income from Other Sources (B3)", format_currency(other_income), "IncomeOthSrc"],
            ["Gross Total Income (B1+B2+B3)", format_currency(computation.get("gross_total_income", 0)), "GrossTotIncome"],
        ]
        
        table = Table(gti_data, colWidths=[75*mm, 45*mm, 60*mm])
        table.setStyle(self._get_table_style())
        story.append(table)
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def _create_deductions_section(self, computation: Dict, documents_data: Dict) -> list:
        """Create Deductions section (Chapter VI-A)"""
        story = []
        story.append(Paragraph("PART C: DEDUCTIONS UNDER CHAPTER VI-A", self.styles['SectionHeader']))
        
        regime = computation.get("recommended_regime", "New Regime")
        
        if regime == "New Regime":
            story.append(Paragraph(
                "Note: Under New Tax Regime, most deductions under Chapter VI-A are NOT available. Only Section 80CCD(2) - Employer contribution to NPS is allowed.",
                self.styles['Instructions']
            ))
            story.append(Spacer(1, 3*mm))
        
        deductions = documents_data.get("old_regime_deductions", {})
        if isinstance(deductions, str):
            deductions = {}
        
        # Calculate 80C combined limit
        sec_80c = deductions.get("80C", 0)
        sec_80ccc = deductions.get("80CCC", 0)
        sec_80ccd1 = deductions.get("80CCD_1", 0)
        total_80c_combined = min(sec_80c + sec_80ccc + sec_80ccd1, self.sec_80c_limit)
        
        deduction_data = [
            ["Section", "Amount Invested", "Eligible Amount", "Maximum Limit", "Portal Reference"],
            ["80C (LIC, PPF, ELSS, etc.)", format_currency(sec_80c), format_currency(min(sec_80c, self.sec_80c_limit)), format_currency(self.sec_80c_limit), "Section80C"],
            ["80CCC (Pension Fund)", format_currency(sec_80ccc), format_currency(min(sec_80ccc, self.sec_80c_limit)), format_currency(self.sec_80c_limit), "Section80CCC"],
            ["80CCD(1) - Employee NPS", format_currency(sec_80ccd1), format_currency(min(sec_80ccd1, self.sec_80c_limit)), "10% of Salary", "Section80CCDEmployeeOrSE"],
            ["Total 80C+80CCC+80CCD(1)", format_currency(sec_80c + sec_80ccc + sec_80ccd1), format_currency(total_80c_combined), format_currency(self.sec_80c_limit), "-"],
            ["80CCD(1B) - Additional NPS", format_currency(deductions.get("80CCD_1B", 0)), format_currency(min(deductions.get("80CCD_1B", 0), self.sec_80ccd1b_limit)), format_currency(self.sec_80ccd1b_limit), "Section80CCD1B"],
            ["80CCD(2) - Employer NPS", format_currency(deductions.get("80CCD_2", 0)), format_currency(deductions.get("80CCD_2", 0)), f"{self.sec_80ccd2_percent}% of Salary", "Section80CCDEmployer"],
            ["80D - Medical Insurance", format_currency(deductions.get("80D", 0)), format_currency(min(deductions.get("80D", 0), self.sec_80d_max)), format_currency(self.sec_80d_max), "Section80D"],
            ["80DD - Disabled Dependent", format_currency(deductions.get("80DD", 0)), format_currency(min(deductions.get("80DD", 0), self.sec_80dd_severe)), format_currency(self.sec_80dd_severe), "Section80DD"],
            ["80DDB - Medical Treatment", format_currency(deductions.get("80DDB", 0)), format_currency(min(deductions.get("80DDB", 0), self.sec_80ddb)), format_currency(self.sec_80ddb), "Section80DDB"],
            ["80E - Education Loan Interest", format_currency(deductions.get("80E", 0)), format_currency(deductions.get("80E", 0)), "No Limit", "Section80E"],
            ["80EE - Home Loan Interest", format_currency(deductions.get("80EE", 0)), format_currency(min(deductions.get("80EE", 0), self.sec_80ee)), format_currency(self.sec_80ee), "Section80EE"],
            ["80EEA - Affordable Housing", format_currency(deductions.get("80EEA", 0)), format_currency(min(deductions.get("80EEA", 0), self.sec_80eea)), format_currency(self.sec_80eea), "Section80EEA"],
            ["80G - Donations", format_currency(deductions.get("80G", 0)), format_currency(deductions.get("80G", 0)), "Varies", "Section80G"],
            ["80GG - Rent Paid", format_currency(deductions.get("80GG", 0)), format_currency(min(deductions.get("80GG", 0), self.sec_80gg_limit)), format_currency(self.sec_80gg_limit), "Section80GG"],
            ["80TTA - Savings Interest", format_currency(deductions.get("80TTA", 0)), format_currency(min(deductions.get("80TTA", 0), self.sec_80tta)), format_currency(self.sec_80tta), "Section80TTA"],
            ["80TTB - Sr. Citizen Interest", format_currency(deductions.get("80TTB", 0)), format_currency(min(deductions.get("80TTB", 0), self.sec_80ttb)), format_currency(self.sec_80ttb), "Section80TTB"],
            ["80U - Self Disability", format_currency(deductions.get("80U", 0)), format_currency(min(deductions.get("80U", 0), self.sec_80u_severe)), format_currency(self.sec_80u_severe), "Section80U"],
        ]
        
        table = Table(deduction_data, colWidths=[45*mm, 32*mm, 32*mm, 28*mm, 43*mm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f3f4f6')),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#fef3c7')),  # Highlight total row
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ]))
        story.append(table)
        story.append(Spacer(1, 3*mm))
        
        # Total Deductions
        total_deductions = computation.get("old_regime_total_deductions", 0) if regime == "Old Regime" else computation.get("new_regime_total_deductions", 0)
        story.append(Paragraph(f"<b>Total Chapter VI-A Deductions: {format_currency(total_deductions)}</b> (TotalChapVIADeductions)", self.styles['Normal']))
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def _create_tax_computation_section(self, computation: Dict) -> list:
        """Create Tax Computation section"""
        story = []
        story.append(Paragraph("PART D: TAX COMPUTATION", self.styles['SectionHeader']))
        
        regime = computation.get("recommended_regime", "New Regime")
        
        # Show computation for recommended regime
        if regime == "Old Regime":
            taxable_income = computation.get("old_regime_taxable_income", 0)
            tax_before_rebate = computation.get("old_regime_tax_before_rebate", 0)
            rebate = computation.get("old_regime_rebate", 0)
            tax_after_rebate = computation.get("old_regime_tax_after_rebate", 0)
            surcharge = computation.get("old_regime_surcharge", 0)
            cess = computation.get("old_regime_cess", 0)
            total_tax = computation.get("old_regime_total_tax", 0)
        else:
            taxable_income = computation.get("new_regime_taxable_income", 0)
            tax_before_rebate = computation.get("new_regime_tax_before_rebate", 0)
            rebate = computation.get("new_regime_rebate", 0)
            tax_after_rebate = computation.get("new_regime_tax_after_rebate", 0)
            surcharge = computation.get("new_regime_surcharge", 0)
            cess = computation.get("new_regime_cess", 0)
            total_tax = computation.get("new_regime_total_tax", 0)
        
        story.append(Paragraph(f"Computing under: {regime}", self.styles['SubHeader']))
        
        # Get rebate max for display
        rebate_max = self.rebate_new_max if regime == "New Regime" else self.rebate_old_max
        
        tax_data = [
            ["ITR-1 Field", "Amount", "Portal Reference"],
            ["Total Income (after deductions)", format_currency(taxable_income), "TotalIncome"],
            ["Tax on Total Income", format_currency(tax_before_rebate), "TotalTaxPayable"],
            ["Rebate u/s 87A", format_currency(rebate), f"Rebate87A (max {format_currency(rebate_max)} for {regime.lower()})"],
            ["Tax After Rebate", format_currency(tax_after_rebate), "TaxPayableOnRebate"],
            ["Surcharge", format_currency(surcharge), "Part of computation"],
            [f"Health & Education Cess ({self.cess_percent}%)", format_currency(cess), "EducationCess"],
            ["Total Tax Liability", format_currency(total_tax), "GrossTaxLiability"],
            ["Relief u/s 89", format_currency(computation.get("relief_89", 0)), "Section89"],
            ["Net Tax Liability", format_currency(total_tax), "NetTaxLiability"],
        ]
        
        table = Table(tax_data, colWidths=[75*mm, 45*mm, 60*mm])
        table.setStyle(self._get_table_style())
        story.append(table)
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def _create_tds_section(self, computation: Dict, documents_data: Dict) -> list:
        """Create TDS Details section"""
        story = []
        story.append(Paragraph("PART E: TAXES PAID", self.styles['SectionHeader']))
        
        total_tds = computation.get("total_tds", 0)
        tds_salary = documents_data.get("tds_on_salary", 0)
        advance_tax = documents_data.get("advance_tax_paid", 0)
        self_assessment = documents_data.get("self_assessment_tax", 0)
        tcs = 0  # Tax Collected at Source
        
        tds_data = [
            ["Tax Type", "Amount", "Portal Reference"],
            ["TDS on Salary (as per Form 16)", format_currency(tds_salary), "TDSonSalaries > TotalTDSonSalaries"],
            ["TDS on Other than Salary", format_currency(total_tds - tds_salary), "TDSonOthThanSals > TotalTDSonOthThanSals"],
            ["Tax Collected at Source (TCS)", format_currency(tcs), "ScheduleTCS > TotalSchTCS"],
            ["Advance Tax Paid", format_currency(advance_tax), "TaxPayments > TotalTaxPayments"],
            ["Self Assessment Tax", format_currency(self_assessment), "Included in TaxPayments"],
            ["Total Taxes Paid", format_currency(total_tds + advance_tax + self_assessment), "TaxesPaid > TotalTaxesPaid"],
        ]
        
        table = Table(tds_data, colWidths=[75*mm, 45*mm, 60*mm])
        table.setStyle(self._get_table_style())
        story.append(table)
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def _create_final_tax_section(self, computation: Dict) -> list:
        """Create Final Tax/Refund section"""
        story = []
        story.append(Paragraph("PART F: TAX PAYABLE OR REFUND", self.styles['SectionHeader']))
        
        regime = computation.get("recommended_regime", "New Regime")
        total_tax = computation.get("new_regime_total_tax", 0) if regime == "New Regime" else computation.get("old_regime_total_tax", 0)
        total_tds = computation.get("total_tds", 0)
        tax_payable = computation.get("tax_payable", 0)
        refund = computation.get("refund_amount", 0)
        
        final_data = [
            ["Description", "Amount", "Portal Reference"],
            ["Total Tax Liability", format_currency(total_tax), "NetTaxLiability + Interest"],
            ["Interest u/s 234A (Late Filing)", "Rs.0", "IntrstPay > IntrstPayUs234A"],
            ["Interest u/s 234B (Advance Tax)", "Rs.0", "IntrstPay > IntrstPayUs234B"],
            ["Interest u/s 234C (Installment)", "Rs.0", "IntrstPay > IntrstPayUs234C"],
            ["Late Filing Fee u/s 234F", "Rs.0", "IntrstPay > LateFilingFee234F"],
            ["Total Tax + Interest", format_currency(total_tax), "TotTaxPlusIntrstPay"],
            ["Total Taxes Paid", format_currency(total_tds), "TaxesPaid > TotalTaxesPaid"],
        ]
        
        table = Table(final_data, colWidths=[75*mm, 45*mm, 60*mm])
        table.setStyle(self._get_table_style())
        story.append(table)
        story.append(Spacer(1, 5*mm))
        
        # Highlight Result
        if refund > 0:
            result_text = f"REFUND DUE: {format_currency(refund)}"
            bg_color = colors.HexColor('#dcfce7')
            text_color = colors.HexColor('#166534')
            portal_ref = "Refund > RefundDue"
        else:
            result_text = f"TAX PAYABLE: {format_currency(tax_payable)}"
            bg_color = colors.HexColor('#fef2f2')
            text_color = colors.HexColor('#991b1b')
            portal_ref = "TaxPaid > BalTaxPayable"
        
        result_data = [[result_text, portal_ref]]
        result_table = Table(result_data, colWidths=[120*mm, 60*mm])
        result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('TEXTCOLOR', (0, 0), (0, 0), text_color),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(result_table)
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def _create_instructions_section(self, computation: Dict) -> list:
        """Create filing instructions"""
        story = []
        story.append(Paragraph("FILING INSTRUCTIONS", self.styles['SectionHeader']))
        
        instructions = [
            "1. Login to the Income Tax e-Filing portal: https://www.incometax.gov.in",
            "2. Go to 'e-File' → 'Income Tax Returns' → 'File Income Tax Return'",
            "3. Select Assessment Year, Filing Type (Original), and ITR Form (ITR-1 SAHAJ)",
            "4. Fill in Personal Information as per Part A of this report",
            "5. Enter Income Details as per Part B (Salary, House Property, Other Sources)",
            "6. Enter Deductions if opting for Old Regime as per Part C",
            "7. Verify Tax Computation matches Part D",
            "8. Add Bank Account details for refund if applicable",
            "9. Verify all TDS entries match with Form 26AS",
            "10. Preview, Submit and e-Verify using Aadhaar OTP or DSC",
        ]
        
        for instruction in instructions:
            story.append(Paragraph(instruction, self.styles['Normal']))
            story.append(Spacer(1, 2*mm))
        
        story.append(Spacer(1, 5*mm))
        
        # Disclaimer
        story.append(Paragraph("DISCLAIMER", self.styles['SubHeader']))
        disclaimer = """This report is a helper document generated based on AI analysis of your uploaded tax documents. 
        It is meant to assist in filing your ITR-1 and should be verified against your actual documents. 
        The final responsibility of accurate filing lies with the taxpayer. Please consult a qualified CA for complex tax situations."""
        story.append(Paragraph(disclaimer, self.styles['Instructions']))
        
        # Footer with timestamp
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph(f"<i>Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", self.styles['Instructions']))
        story.append(Paragraph("<i>Generated by AI-CA Virtual Chartered Accountant</i>", self.styles['Instructions']))
        
        return story
    
    def _get_table_style(self) -> TableStyle:
        """Get standard table style"""
        return TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f3f4f6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])


def generate_helper_report(
    user_data: Dict[str, Any],
    computation: Dict[str, Any],
    documents_data: Dict[str, Any],
    financial_year: str,
    tax_rules: Optional[Dict[str, Any]] = None
) -> BytesIO:
    """
    Convenience function to generate Helper Report PDF
    
    Args:
        user_data: User personal information
        computation: Tax computation result from database
        documents_data: Aggregated data from documents
        financial_year: FY like "2024-25"
        tax_rules: Tax rules from RulesService (optional)
    
    Returns:
        BytesIO buffer containing the PDF
    """
    generator = ITR1PDFGenerator(tax_rules=tax_rules)
    return generator.generate_pdf(user_data, computation, documents_data, financial_year)
