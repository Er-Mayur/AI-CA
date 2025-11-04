# backend/core/tax_engine.py
from schemas.tax_schemas import StructuredTaxDoc

CESS_RATE = 0.04

def tax_old_regime(total_taxable: float) -> float:
    tax = 0.0
    slabs = [(250000, 0.0), (250000, 0.05), (500000, 0.20)]
    remaining = total_taxable

    # 0–2.5L
    take = min(remaining, slabs[0][0]); remaining -= take
    # 2.5–5L
    take = min(max(remaining, 0), slabs[1][0]); tax += take * slabs[1][1]; remaining -= take
    # 5–10L
    take = min(max(remaining, 0), slabs[2][0]); tax += take * slabs[2][1]; remaining -= take
    # >10L
    if remaining > 0: tax += remaining * 0.30

    return tax * (1 + CESS_RATE)

def tax_new_regime(total_income: float) -> float:
    tax = 0.0
    br = [
        (300000, 0.00),
        (300000, 0.05),
        (300000, 0.10),
        (300000, 0.15),
        (300000, 0.20),
    ]
    remaining = total_income
    for width, rate in br:
        take = min(max(remaining, 0), width)
        tax += take * rate
        remaining -= take
    if remaining > 0:
        tax += remaining * 0.30
    return tax * (1 + CESS_RATE)

def compute_tax(doc: StructuredTaxDoc):
    # Salary
    gross = (doc.salary.gross_salary_17_1 or 0) + (doc.salary.perquisites_17_2 or 0) + (doc.salary.profits_in_lieu_17_3 or 0)
    exempt = sum(doc.salary.exempt_allowances_sec10.values()) if doc.salary.exempt_allowances_sec10 else 0.0
    std_ded = doc.salary.standard_deduction or 0.0
    prof_tax = doc.salary.professional_tax_16_iii or 0.0

    # Old regime salary income: gross - exemptions - std - prof tax
    salary_old = max(gross - exempt - std_ded - prof_tax, 0.0)

    # New regime salary income: gross - std (std allowed from FY 24-25)
    salary_new = max(gross - std_ded, 0.0)

    # Other income
    other = doc.other_income.savings_interest + doc.other_income.fd_interest + doc.other_income.dividend + doc.other_income.others

    # Old regime deductions
    ded = doc.deductions.total

    # Taxable
    taxable_old = max(salary_old + other - ded, 0.0)
    taxable_new = max(salary_new + other, 0.0)

    tax_old = tax_old_regime(taxable_old)
    tax_new = tax_new_regime(taxable_new)

    chosen = "old" if tax_old < tax_new else "new"
    tax_payable = min(tax_old, tax_new)

    credits = (doc.credits.tds_salary_192 + doc.credits.tds_other +
               doc.credits.adv_tax + doc.credits.self_assessment_tax)

    net_payable = round(tax_payable - credits, 2)

    return {
        "gross_salary": round(gross, 2),
        "exemptions_sec10": round(exempt, 2),
        "standard_deduction": round(std_ded, 2),
        "professional_tax": round(prof_tax, 2),
        "other_income": round(other, 2),
        "deductions_via_old": round(ded, 2),

        "taxable_income_old": round(taxable_old, 2),
        "taxable_income_new": round(taxable_new, 2),

        "tax_old": round(tax_old, 2),
        "tax_new": round(tax_new, 2),
        "best_regime": chosen,
        "tax_payable": round(tax_payable, 2),
        "total_credits": round(credits, 2),
        "net_payable_or_refund": net_payable
    }
