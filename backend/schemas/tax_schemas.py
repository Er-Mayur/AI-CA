# backend/schemas/tax_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict

class Identity(BaseModel):
    employee_name: Optional[str] = None
    employee_pan: Optional[str] = None
    employer_name: Optional[str] = None
    employer_pan: Optional[str] = None
    employer_tan: Optional[str] = None
    assessment_year: Optional[str] = None
    financial_year: Optional[str] = None
    doc_type: Optional[str] = None

class SalaryBlock(BaseModel):
    gross_salary_17_1: Optional[float] = None
    perquisites_17_2: Optional[float] = None
    profits_in_lieu_17_3: Optional[float] = None
    exempt_allowances_sec10: Dict[str, float] = Field(default_factory=dict)
    standard_deduction: Optional[float] = None
    professional_tax_16_iii: Optional[float] = None
    taxable_salary: Optional[float] = None
    tds_on_salary: Optional[float] = None
    relief_89_1: Optional[float] = None

class OtherIncome(BaseModel):
    savings_interest: float = 0.0
    fd_interest: float = 0.0
    dividend: float = 0.0
    others: float = 0.0

class ChapterVIA(BaseModel):
    sec_80c: float = 0.0
    sec_80ccd_1b: float = 0.0
    sec_80d: float = 0.0
    sec_80tta: float = 0.0
    total: float = 0.0

class Credits(BaseModel):
    tds_salary_192: float = 0.0
    tds_other: float = 0.0
    tcs_total: float = 0.0
    adv_tax: float = 0.0
    self_assessment_tax: float = 0.0
    refund_issued: float = 0.0

class StructuredTaxDoc(BaseModel):
    identity: Identity
    salary: SalaryBlock
    other_income: OtherIncome
    deductions: ChapterVIA
    credits: Credits
