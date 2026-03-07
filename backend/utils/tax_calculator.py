"""
Tax Calculator Module
All tax figures are loaded from the database rules - NO HARDCODED VALUES.
Rules are based on official government tax website.
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from models import TaxRule
from utils.rules_service import RulesService, TaxRulesNotFoundError
from utils.itr_form_detector import detect_itr_form, ITRFormDetector
import json

def get_tax_rules(db: Session, financial_year: str) -> Dict[str, Any]:
    """Get tax rules for a specific financial year"""
    tax_rule = db.query(TaxRule).filter(
        TaxRule.financial_year == financial_year,
        TaxRule.is_active == True
    ).first()
    
    if not tax_rule:
        # Try to get default rules
        default_rule = db.query(TaxRule).filter(
            TaxRule.is_active == True
        ).order_by(TaxRule.financial_year.desc()).first()
        
        if default_rule:
            print(f"⚠️ Using rules for FY {default_rule.financial_year} (requested: {financial_year})")
            return default_rule.rules_json
        
        raise Exception(f"Tax rules for FY {financial_year} not found. Please seed the database.")
    
    return tax_rule.rules_json

def calculate_age(date_of_birth: datetime) -> int:
    """Calculate age from date of birth as of end of financial year"""
    # Age is typically calculated as on March 31 of the assessment year
    today = datetime.now()
    age = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    return age

def get_age_category(age: int) -> str:
    """Determine age category for tax slab"""
    if age < 60:
        return "individual_below_60"
    elif age < 80:
        return "individual_60_to_79"
    else:
        return "individual_80_and_above"

def calculate_tax_by_slab_accurate(income: float, slabs: List[Dict[str, Any]]) -> Tuple[float, List[Dict]]:
    """
    Calculate tax based on slab rates with detailed breakdown
    Returns: (total_tax, slab_breakdown)
    """
    tax = 0.0
    breakdown = []
    remaining_income = income
    
    # Handle different slab formats
    for i, slab in enumerate(slabs):
        # Determine slab boundaries
        lower = 0
        upper = float('inf')
        rate = 0
        
        # Parse slab format
        if "min" in slab and "max" in slab:
            # Format: {"min": 0, "max": 250000, "rate_percent": 0}
            lower = slab["min"]
            upper = slab["max"] if slab["max"] is not None else float('inf')
            rate = slab.get("rate_percent", 0)
        elif "upto" in slab:
            # Format: {"upto": 250000, "rate_percent": 0}
            lower = 0
            upper = slab["upto"]
            rate = slab.get("rate_percent", 0)
        elif "over" in slab:
            lower = slab["over"]
            upper = slab.get("up_to", float('inf'))
            if upper is None:
                upper = float('inf')
            rate = slab.get("rate_percent", 0)
        else:
            continue
        
        # Calculate tax for this slab
        if income > lower:
            taxable_in_slab = min(income, upper) - lower
            if taxable_in_slab > 0:
                slab_tax = taxable_in_slab * rate / 100
                tax += slab_tax
                
                breakdown.append({
                    "slab": f"₹{lower:,.0f} - ₹{upper:,.0f}" if upper != float('inf') else f"Above ₹{lower:,.0f}",
                    "taxable_amount": taxable_in_slab,
                    "rate": f"{rate}%",
                    "tax": slab_tax
                })
    
    return tax, breakdown

def calculate_tax_by_slab(income: float, slabs: List[Dict[str, Any]]) -> float:
    """Calculate tax based on slab rates (backward compatible)"""
    tax, _ = calculate_tax_by_slab_accurate(income, slabs)
    return tax

def apply_deduction_limits(deductions: Dict[str, float], age: int, gross_salary: float, rules_service: RulesService) -> Dict[str, float]:
    """
    Apply statutory limits to deductions based on tax rules
    All limits are fetched from RulesService - NO hardcoded values
    Returns capped deductions
    """
    # Get all limits from rules service
    limits = rules_service.get_all_deduction_limits(age)
    
    capped = {}
    
    # 80C group (80C + 80CCC + 80CCD(1)) - Combined limit from rules
    section_80c_total = (
        deductions.get("80C", 0) +
        deductions.get("80CCC", 0) +
        deductions.get("80CCD_1", 0)
    )
    capped["80C_total"] = min(section_80c_total, limits["80C"])
    
    # 80CCD(1B) - Additional NPS limit from rules
    capped["80CCD_1B"] = min(deductions.get("80CCD_1B", 0), limits["80CCD_1B"])
    
    # 80CCD(2) - Employer NPS, max % of basic salary from rules
    max_80ccd2_percent = limits.get("80CCD_2_percent", 10) / 100
    max_80ccd2 = gross_salary * max_80ccd2_percent
    capped["80CCD_2"] = min(deductions.get("80CCD_2", 0), max_80ccd2)
    
    # 80D - Health Insurance - limits based on age from rules
    max_80d_self = limits["80D_self"]
    max_80d_parents = limits["80D_parents_senior"]  # Assuming parents could be senior
    capped["80D"] = min(deductions.get("80D", 0), max_80d_self + max_80d_parents)
    
    # 80E - Education Loan Interest - No limit (None in rules)
    capped["80E"] = deductions.get("80E", 0)
    
    # 80G - Donations - variable limit
    capped["80G"] = deductions.get("80G", 0)
    
    # 80GG - Rent Paid (if not receiving HRA) - from rules
    capped["80GG"] = min(deductions.get("80GG", 0), limits["80GG"])
    
    # 80TTA/80TTB - Savings Interest based on age - from rules
    if age >= 60:
        capped["80TTB"] = min(deductions.get("80TTB", 0), limits["80TTB"])
        capped["80TTA"] = 0
    else:
        capped["80TTA"] = min(deductions.get("80TTA", 0), limits["80TTA"])
        capped["80TTB"] = 0
    
    # 80U - Disability - from rules
    capped["80U"] = min(deductions.get("80U", 0), limits["80U_severe"])
    
    # 80DD - Disabled Dependent - from rules
    capped["80DD"] = min(deductions.get("80DD", 0), limits["80DD_severe"])
    
    # 80DDB - Medical Treatment based on age - from rules
    capped["80DDB"] = min(deductions.get("80DDB", 0), limits["80DDB"])
    
    # 80EE/80EEA - First Home Interest - from rules
    capped["80EE"] = min(deductions.get("80EE", 0), limits["80EE"])
    capped["80EEA"] = min(deductions.get("80EEA", 0), limits["80EEA"])
    
    # Section 24(b) - Home Loan Interest - from rules
    capped["24b_home_loan_interest"] = min(
        deductions.get("24b_home_loan_interest", 0), limits["24b"]
    )
    
    # Standard Deduction and Professional Tax - under Section 16 from rules
    capped["Standard Deduction"] = min(deductions.get("Standard Deduction", 0), limits["Standard Deduction"])
    capped["Professional Tax"] = min(deductions.get("Professional Tax", 0), limits["Professional Tax"])
    
    return capped

def calculate_old_regime_tax(
    gross_income: float,
    deductions: Dict[str, float],
    age: int,
    rules_service: RulesService
) -> Dict[str, Any]:
    """Calculate tax under old regime with comprehensive deductions.
    All values loaded from RulesService - NO hardcoded values.
    """
    
    print(f"\n📊 Calculating OLD REGIME tax...")
    print(f"   Gross Income: ₹{gross_income:,.0f}")
    
    # Apply deduction limits using rules service
    capped_deductions = apply_deduction_limits(deductions, age, gross_income, rules_service)
    
    # Calculate total deductions
    total_deductions = sum(v for v in capped_deductions.values() if isinstance(v, (int, float)))
    
    # Cap total deductions at reasonable limit (shouldn't exceed income)
    total_deductions = min(total_deductions, gross_income)
    
    print(f"   Total Deductions: ₹{total_deductions:,.0f}")
    
    # Calculate taxable income
    taxable_income = max(0, gross_income - total_deductions)
    
    print(f"   Taxable Income: ₹{taxable_income:,.0f}")
    
    # Get tax slabs from rules service
    slabs = rules_service.get_slabs("old_regime", age)
    
    # Calculate tax before rebate
    tax_before_rebate, breakdown = calculate_tax_by_slab_accurate(taxable_income, slabs)
    
    # Calculate rebate under section 87A from rules
    rebate = 0.0
    rebate_config = rules_service.get_rebate_87a("old_regime")
    if taxable_income <= rebate_config["max_total_income"]:
        rebate = min(tax_before_rebate, rebate_config["rebate_cap"])
    
    # Tax after rebate
    tax_after_rebate = max(0, tax_before_rebate - rebate)
    
    # Calculate surcharge using rules
    surcharge = calculate_surcharge(taxable_income, tax_after_rebate, rules_service, "old_regime")
    
    # Calculate cess from rules
    cess_percent = rules_service.get_cess_percent()
    cess = (tax_after_rebate + surcharge) * cess_percent / 100
    
    # Total tax
    total_tax = tax_after_rebate + surcharge + cess
    
    return {
        "deductions": deductions,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate": rebate,
        "tax_after_rebate": tax_after_rebate,
        "surcharge": surcharge,
        "cess": cess,
        "total_tax": total_tax
    }

def calculate_new_regime_tax(
    gross_income: float,
    allowed_deductions: Dict[str, float],
    age: int,
    rules_service: RulesService
) -> Dict[str, Any]:
    """Calculate tax under new regime (only limited deductions allowed).
    All values loaded from RulesService - NO hardcoded values.
    """
    
    print(f"\n📊 Calculating NEW REGIME tax...")
    print(f"   Gross Income: ₹{gross_income:,.0f}")
    
    # New regime allows only limited deductions:
    # - Standard Deduction (from rules)
    # - 80CCD(2): Employer NPS contribution
    # - 80CCH: Agnipath Scheme
    # - Family Pension deduction under section 57(iia)
    
    # Get standard deduction from rules service
    std_ded_limit = rules_service.get_standard_deduction("new_regime")
    standard_deduction = min(allowed_deductions.get("Standard Deduction", std_ded_limit), std_ded_limit)
    employer_nps = allowed_deductions.get("80CCD_2", 0)
    
    total_deductions = standard_deduction + employer_nps
    
    print(f"   Allowed Deductions: ₹{total_deductions:,.0f}")
    print(f"      Standard Deduction: ₹{standard_deduction:,.0f}")
    print(f"      Employer NPS (80CCD(2)): ₹{employer_nps:,.0f}")
    
    # Calculate taxable income
    taxable_income = max(0, gross_income - total_deductions)
    
    print(f"   Taxable Income: ₹{taxable_income:,.0f}")
    
    # Get new regime slabs from rules service
    slabs = rules_service.get_slabs("new_regime", age)
    
    # Calculate tax before rebate
    tax_before_rebate, breakdown = calculate_tax_by_slab_accurate(taxable_income, slabs)
    
    # Calculate rebate under section 87A from rules
    rebate = 0.0
    rebate_config = rules_service.get_rebate_87a("new_regime")
    if taxable_income <= rebate_config["max_total_income"]:
        rebate = min(tax_before_rebate, rebate_config["rebate_cap"])
    
    # Tax after rebate
    tax_after_rebate = max(0, tax_before_rebate - rebate)
    
    # Calculate surcharge using rules
    surcharge = calculate_surcharge(taxable_income, tax_after_rebate, rules_service, "new_regime")
    
    # Calculate cess from rules
    cess_percent = rules_service.get_cess_percent()
    cess = (tax_after_rebate + surcharge) * cess_percent / 100
    
    # Total tax
    total_tax = tax_after_rebate + surcharge + cess
    
    print(f"   Tax Before Rebate: ₹{tax_before_rebate:,.0f}")
    print(f"   Rebate 87A: ₹{rebate:,.0f}")
    print(f"   Surcharge: ₹{surcharge:,.0f}")
    print(f"   Cess: ₹{cess:,.0f}")
    print(f"   Total Tax: ₹{total_tax:,.0f}")
    
    return {
        "deductions": {"Standard Deduction": standard_deduction, "80CCD(2)": employer_nps},
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate": rebate,
        "tax_after_rebate": tax_after_rebate,
        "surcharge": surcharge,
        "cess": cess,
        "total_tax": total_tax,
        "slab_breakdown": breakdown
    }


def calculate_surcharge(income: float, tax: float, rules_service: RulesService, regime: str) -> float:
    """Calculate surcharge based on income slabs with marginal relief.
    Thresholds loaded from RulesService - NO hardcoded values.
    """
    
    # Get surcharge thresholds from rules service
    thresholds = rules_service.get_surcharge_thresholds(regime)
    
    if not thresholds:
        return 0.0
    
    surcharge_rate = 0
    applicable_threshold = 0
    
    for threshold in thresholds:
        if income > threshold["min_exclusive"]:
            surcharge_rate = threshold["rate_percent"]
            applicable_threshold = threshold["min_exclusive"]
    
    if surcharge_rate == 0:
        return 0.0
    
    surcharge = tax * surcharge_rate / 100
    
    # Apply marginal relief
    # The total tax after surcharge should not exceed the income above the threshold
    # plus the tax on threshold income
    if applicable_threshold > 0:
        excess_income = income - applicable_threshold
        if surcharge > excess_income:
            surcharge = excess_income  # Marginal relief applied
    
    return surcharge

def recommend_regime(
    old_regime_result: Dict[str, Any],
    new_regime_result: Dict[str, Any]
) -> Tuple[str, str, float]:
    """Recommend the best regime and provide explanation"""
    
    old_tax = old_regime_result["total_tax"]
    new_tax = new_regime_result["total_tax"]
    
    if new_tax < old_tax:
        regime = "New Regime"
        savings = old_tax - new_tax
        reason = f"""New Regime is recommended as it results in lower tax liability.
        
Tax under Old Regime: ₹{old_tax:,.2f}
Tax under New Regime: ₹{new_tax:,.2f}
Tax Savings: ₹{savings:,.2f}

Even though the new regime doesn't allow most deductions, the lower tax rates result in overall tax savings for your income level."""
    else:
        regime = "Old Regime"
        savings = new_tax - old_tax
        reason = f"""Old Regime is recommended as it results in lower tax liability.

Tax under Old Regime: ₹{old_tax:,.2f}
Tax under New Regime: ₹{new_tax:,.2f}
Tax Savings: ₹{savings:,.2f}

The deductions available under the old regime (₹{old_regime_result['total_deductions']:,.2f}) outweigh the benefits of lower tax rates in the new regime."""
    
    return regime, reason, savings

def recommend_itr_form(
    aggregated_data: Dict[str, Any],
    user_data: Dict[str, Any] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Recommend appropriate ITR form using comprehensive detection logic
    
    Uses ITRFormDetector to analyze:
    - Income signals from documents
    - TDS section codes
    - Eligibility indicators (foreign assets, director status, etc.)
    
    Returns:
        Tuple of (itr_form, reason, detection_details)
    """
    # Use the comprehensive ITR form detector
    detection_result = detect_itr_form(aggregated_data, user_data)
    
    return (
        detection_result["itr_form"],
        detection_result["reason"],
        detection_result
    )

def calculate_comprehensive_tax(
    user_data: Dict[str, Any],
    extracted_data: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    Comprehensive tax calculation combining data from all documents.
    All tax figures loaded from RulesService - NO hardcoded values.
    """
    
    print(f"\n{'='*60}")
    print(f"🧮 COMPREHENSIVE TAX CALCULATION")
    print(f"{'='*60}")
    
    financial_year = user_data.get("financial_year", "2024-25")
    dob = user_data.get("date_of_birth")
    age = calculate_age(dob) if dob else 30  # Default age if not provided
    
    print(f"Financial Year: {financial_year}")
    print(f"User Age: {age}")
    
    # Create RulesService for the financial year
    rules_service = RulesService(db, financial_year)
    rules = rules_service.rules  # Get raw rules for assessment year lookup
    
    # Determine assessment year
    assessment_year = rules.get("assessment_year")
    if not assessment_year and financial_year:
        # Calculate AY from FY
        try:
            fy_parts = financial_year.split("-")
            ay_start = int(fy_parts[0]) + 1
            ay_end = int(fy_parts[1]) + 1
            assessment_year = f"{ay_start}-{ay_end:02d}"
        except:
            assessment_year = financial_year
    
    # Aggregate income from all sources
    gross_income = extracted_data.get("gross_total_income", 0)
    salary_income = extracted_data.get("salary_income", 0)
    
    # If gross_total_income is 0 but salary_income exists, use salary
    if gross_income == 0 and salary_income > 0:
        gross_income = salary_income
    
    print(f"Gross Total Income: ₹{gross_income:,.0f}")
    
    # === OLD REGIME DEDUCTIONS ===
    old_regime_deductions = extracted_data.get("old_regime_deductions", {})
    
    # Add exemptions if not already in deductions
    exemptions = extracted_data.get("exemptions", {})
    if isinstance(exemptions, dict):
        if exemptions.get("standard_deduction", 0) > 0:
            old_regime_deductions["Standard Deduction"] = max(
                old_regime_deductions.get("Standard Deduction", 0),
                exemptions.get("standard_deduction", 0)
            )
        if exemptions.get("professional_tax", 0) > 0:
            old_regime_deductions["Professional Tax"] = max(
                old_regime_deductions.get("Professional Tax", 0),
                exemptions.get("professional_tax", 0)
            )
    
    # Ensure minimum standard deduction for salaried - from rules
    if salary_income > 0 and old_regime_deductions.get("Standard Deduction", 0) == 0:
        std_ded = rules_service.get_standard_deduction("old_regime")
        old_regime_deductions["Standard Deduction"] = std_ded
        print(f"   Applied Standard Deduction from rules: ₹{std_ded:,}")
    
    print(f"Old Regime Deductions: {sum(v for v in old_regime_deductions.values() if isinstance(v, (int, float)))}")
    
    # === NEW REGIME DEDUCTIONS (Limited) ===
    # Standard Deduction amount from rules
    new_std_deduction = rules_service.get_standard_deduction("new_regime")
    
    new_regime_deductions = {
        "Standard Deduction": new_std_deduction,
        "80CCD_2": old_regime_deductions.get("80CCD_2", 0),  # Employer NPS
        "80CCH": old_regime_deductions.get("80CCH", 0),  # Agnipath
    }
    
    # === CALCULATE TAX UNDER BOTH REGIMES using RulesService ===
    old_regime_result = calculate_old_regime_tax(
        gross_income, old_regime_deductions, age, rules_service
    )
    
    new_regime_result = calculate_new_regime_tax(
        gross_income, new_regime_deductions, age, rules_service
    )
    
    # === RECOMMEND REGIME ===
    recommended_regime, reason, savings = recommend_regime(
        old_regime_result, new_regime_result
    )
    
    print(f"\n📋 RECOMMENDATION: {recommended_regime}")
    print(f"   Tax Savings: ₹{savings:,.0f}")
    
    # === RECOMMEND ITR FORM ===
    # Use comprehensive ITR form detection based on document data
    itr_form, itr_reason, itr_detection = recommend_itr_form(
        extracted_data,
        user_data
    )
    
    print(f"   Recommended ITR Form: {itr_form}")
    print(f"   Detection Confidence: {itr_detection.get('confidence', 'unknown')}")
    
    # Log any warnings from detection
    itr_warnings = itr_detection.get("warnings", [])
    if itr_warnings:
        for warning in itr_warnings:
            print(f"   ⚠️ {warning}")
    
    # === CALCULATE FINAL TAX LIABILITY ===
    total_tds = extracted_data.get("total_tds", 0)
    advance_tax = extracted_data.get("advance_tax_paid", 0)
    self_assessment_tax = extracted_data.get("self_assessment_tax", 0)
    
    total_taxes_paid = total_tds + advance_tax + self_assessment_tax
    
    # Use recommended regime's tax
    if recommended_regime == "New Regime":
        final_tax = new_regime_result["total_tax"]
    else:
        final_tax = old_regime_result["total_tax"]
    
    tax_payable = max(0, final_tax - total_taxes_paid)
    refund_amount = max(0, total_taxes_paid - final_tax)
    
    print(f"\n📊 FINAL COMPUTATION:")
    print(f"   Final Tax (Based on {recommended_regime}): ₹{final_tax:,.0f}")
    print(f"   Total TDS/Taxes Paid: ₹{total_taxes_paid:,.0f}")
    if tax_payable > 0:
        print(f"   Tax Payable: ₹{tax_payable:,.0f}")
    else:
        print(f"   Refund Due: ₹{refund_amount:,.0f}")
    
    print(f"{'='*60}\n")
    
    return {
        "financial_year": financial_year,
        "assessment_year": assessment_year,
        "gross_total_income": gross_income,
        "salary_income": salary_income,
        "old_regime": old_regime_result,
        "new_regime": new_regime_result,
        "recommended_regime": recommended_regime,
        "recommendation_reason": reason,
        "recommended_itr_form": itr_form,
        "itr_form_reason": itr_reason,
        "itr_form_detection": itr_detection,
        "tax_savings": savings,
        "total_tds": total_tds,
        "advance_tax_paid": advance_tax,
        "self_assessment_tax": self_assessment_tax,
        "total_taxes_paid": total_taxes_paid,
        "tax_payable": tax_payable,
        "refund_amount": refund_amount
    }

