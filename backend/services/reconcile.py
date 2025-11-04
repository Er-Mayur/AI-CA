# backend/services/reconcile.py
from schemas.tax_schemas import StructuredTaxDoc

def reconcile_priority(primary: StructuredTaxDoc, secondary: StructuredTaxDoc) -> StructuredTaxDoc:
    """
    Simple priority merge:
    - Identity fields: prefer Form 16 for employer/salary, AIS for other-income granularity.
    - Credits: max of the two for each component, unless clearly additive (e.g., TDS other).
    """
    a, b = primary, secondary

    # Salary block: prefer whichever has gross_salary_17_1
    if not a.salary.gross_salary_17_1 and b.salary.gross_salary_17_1:
        a.salary = b.salary

    # Other income: additive
    a.other_income.savings_interest += b.other_income.savings_interest
    a.other_income.fd_interest      += b.other_income.fd_interest
    a.other_income.dividend         += b.other_income.dividend
    a.other_income.others           += b.other_income.others

    # Deductions: take max per section (Form16 usually authoritative)
    a.deductions.sec_80c      = max(a.deductions.sec_80c, b.deductions.sec_80c)
    a.deductions.sec_80ccd_1b = max(a.deductions.sec_80ccd_1b, b.deductions.sec_80ccd_1b)
    a.deductions.sec_80d      = max(a.deductions.sec_80d, b.deductions.sec_80d)
    a.deductions.sec_80tta    = max(a.deductions.sec_80tta, b.deductions.sec_80tta)
    a.deductions.total = a.deductions.sec_80c + a.deductions.sec_80ccd_1b + a.deductions.sec_80d + a.deductions.sec_80tta

    # Credits: additive for TDS-other, but TDS-salary should align with Form16 if present
    if not a.credits.tds_salary_192 and b.credits.tds_salary_192:
        a.credits.tds_salary_192 = b.credits.tds_salary_192
    a.credits.tds_other          += b.credits.tds_other
    a.credits.tcs_total           = max(a.credits.tcs_total, b.credits.tcs_total)
    a.credits.adv_tax            += b.credits.adv_tax
    a.credits.self_assessment_tax+= b.credits.self_assessment_tax
    a.credits.refund_issued       = max(a.credits.refund_issued, b.credits.refund_issued)

    return a
