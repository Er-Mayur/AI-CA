from typing import Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from models import TaxRule
import json

# Default deduction limits (used as fallback if rules not found)
# These are FY-specific and should be loaded from database rules
DEFAULT_DEDUCTION_LIMITS = {
    "80C": 150000,       # Section 80C (including 80CCC and 80CCD(1))
    "80CCC": 150000,     # Part of 80C limit
    "80CCD_1": 150000,   # Part of 80C limit
    "80CCD_1B": 50000,   # Additional NPS (over and above 80C)
    "80CCD_2": None,     # Employer NPS - No fixed limit (10%/14% of salary)
    "80D_self": 25000,   # Health insurance - Self/Family
    "80D_parents": 25000, # Health insurance - Parents (50000 if senior citizen)
    "80D_preventive": 5000, # Part of 80D limit
    "80DD": 75000,       # Disabled dependent (125000 for severe)
    "80DDB": 40000,      # Medical treatment (100000 for senior citizen)
    "80E": None,         # Education loan interest - No limit
    "80EE": 50000,       # First home loan interest
    "80EEA": 150000,     # Affordable housing interest
    "80G": None,         # Donations - Usually 50% or 100% of donation
    "80GG": 60000,       # Rent paid (min of 5000/month, 25% salary, rent-10% income)
    "80TTA": 10000,      # Savings interest (non-senior)
    "80TTB": 50000,      # Interest income (senior citizen only)
    "80U": 75000,        # Disability (125000 for severe)
    "24b": 200000,       # Home loan interest (let out: no limit)
    "Standard Deduction": 75000,  # Default for FY 2024-25
}

def get_deduction_limits_from_rules(rules: Dict[str, Any]) -> Dict[str, Any]:
    """Extract deduction limits from tax rules JSON"""
    limits = DEFAULT_DEDUCTION_LIMITS.copy()
    
    try:
        deductions = rules.get("deductions", {})
        common = rules.get("common_deductions_exemptions", {})
        
        # Standard Deduction from common_deductions_exemptions
        if "standard_deduction_salaried" in common:
            limits["Standard Deduction"] = common["standard_deduction_salaried"].get("max_amount", 75000)
        
        # 80C from old_regime deductions
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        if "section_80C_80CCC_80CCD1" in old_regime:
            limits["80C"] = old_regime["section_80C_80CCC_80CCD1"].get("combined_limit", 150000)
        
        # 80CCD(1B) additional NPS
        if "section_80CCD1B" in old_regime:
            limits["80CCD_1B"] = old_regime["section_80CCD1B"].get("additional_limit", 50000)
        elif "80CCD(1B)" in common:
            limits["80CCD_1B"] = common["80CCD(1B)"].get("max_amount", 50000)
        
        # 80D Health Insurance
        if "section_80D_health_insurance" in old_regime:
            d80 = old_regime["section_80D_health_insurance"]
            limits["80D_self"] = d80.get("self_family", {}).get("limit", 25000)
            limits["80D_parents"] = d80.get("parents", {}).get("limit", 25000)
            limits["80D_senior"] = d80.get("self_family", {}).get("senior_citizen_limit", 50000)
        elif "80D" in common:
            limits["80D_self"] = common["80D"].get("max_amount_self_family", 25000)
            limits["80D_parents"] = common["80D"].get("max_amount_parents", 25000)
        
        # 80TTA / 80TTB
        if "section_80TTA_savings_interest_non_senior" in old_regime:
            limits["80TTA"] = old_regime["section_80TTA_savings_interest_non_senior"].get("limit", 10000)
        elif "80TTA" in common:
            limits["80TTA"] = common["80TTA"].get("max_amount", 10000)
        
        if "section_80TTB_deposit_interest_senior" in old_regime:
            limits["80TTB"] = old_regime["section_80TTB_deposit_interest_senior"].get("limit", 50000)
        elif "80TTB" in common:
            limits["80TTB"] = common["80TTB"].get("max_amount", 50000)
        
        # 80U Disability
        if "section_80U_taxpayer_with_disability" in old_regime:
            u80 = old_regime["section_80U_taxpayer_with_disability"]
            limits["80U"] = u80.get("regular_disability", 75000)
            limits["80U_severe"] = u80.get("severe_disability_80_percent_or_more", 125000)
        
        # 80DD Disabled Dependent
        if "section_80DD_disabled_dependent" in old_regime:
            dd = old_regime["section_80DD_disabled_dependent"]
            limits["80DD"] = dd.get("regular_disability", 75000)
            limits["80DD_severe"] = dd.get("severe_disability_80_percent_or_more", 125000)
        
        # 80DDB Medical Treatment
        if "section_80DDB_specified_diseases" in old_regime:
            ddb = old_regime["section_80DDB_specified_diseases"]
            limits["80DDB"] = ddb.get("non_senior_citizen_limit", 40000)
            limits["80DDB_senior"] = ddb.get("senior_citizen_limit", 100000)
        
        # 80EE / 80EEA Home Loan
        if "section_80EE_home_loan_interest_extra" in old_regime:
            limits["80EE"] = old_regime["section_80EE_home_loan_interest_extra"].get("limit", 50000)
        if "section_80EEA_first_time_home_buyer_interest" in old_regime:
            limits["80EEA"] = old_regime["section_80EEA_first_time_home_buyer_interest"].get("limit", 150000)
        
        # 80GG Rent
        if "section_80GG_rent_no_hra" in old_regime:
            # 80GG is min of 3 values, but has a max of Rs. 60,000 (5000*12)
            limits["80GG"] = 60000
        
        # Section 24(b) Home Loan Interest
        if "section_24b_house_property_interest" in old_regime:
            so = old_regime["section_24b_house_property_interest"].get("self_occupied", [])
            if so and len(so) > 0:
                limits["24b"] = so[0].get("limit", 200000)
        
    except Exception as e:
        print(f"⚠️ Error extracting deduction limits from rules: {e}")
    
    return limits

def get_standard_deduction_from_rules(rules: Dict[str, Any], regime: str = "new_regime") -> int:
    """Get standard deduction amount from rules based on regime"""
    try:
        # Check common_deductions_exemptions first
        common = rules.get("common_deductions_exemptions", {})
        if "standard_deduction_salaried" in common:
            std_ded = common["standard_deduction_salaried"]
            regimes_allowed = std_ded.get("regimes_allowed", [])
            if regime in regimes_allowed or "new_regime" in regimes_allowed:
                return std_ded.get("max_amount", 75000)
        
        # For new regime, check if standard deduction is mentioned
        # FY 2024-25: Rs. 75,000 for both regimes
        # FY 2023-24: Rs. 50,000
        fy = rules.get("financial_year", "2024-25")
        if fy >= "2024-25":
            return 75000
        else:
            return 50000
            
    except Exception:
        return 75000  # Default for FY 2024-25

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

def apply_deduction_limits(deductions: Dict[str, float], age: int, gross_salary: float, rules: Dict[str, Any] = None) -> Dict[str, float]:
    """
    Apply statutory limits to deductions based on tax rules
    Returns capped deductions
    """
    # Get limits from rules or use defaults
    limits = get_deduction_limits_from_rules(rules) if rules else DEFAULT_DEDUCTION_LIMITS
    
    capped = {}
    
    # 80C group (80C + 80CCC + 80CCD(1)) - Max as per rules (usually 1.5 Lakh)
    section_80c_total = (
        deductions.get("80C", 0) +
        deductions.get("80CCC", 0) +
        deductions.get("80CCD_1", 0)
    )
    capped["80C_total"] = min(section_80c_total, limits.get("80C", 150000))
    
    # 80CCD(1B) - Additional NPS
    capped["80CCD_1B"] = min(deductions.get("80CCD_1B", 0), limits.get("80CCD_1B", 50000))
    
    # 80CCD(2) - Employer NPS, max 10% of basic salary (14% for govt)
    max_80ccd2 = gross_salary * 0.10  # 10% of salary
    capped["80CCD_2"] = min(deductions.get("80CCD_2", 0), max_80ccd2)
    
    # 80D - Health Insurance based on age
    max_80d_self = limits.get("80D_senior", 50000) if age >= 60 else limits.get("80D_self", 25000)
    max_80d_parents = limits.get("80D_senior", 50000)  # Assuming parents could be senior
    capped["80D"] = min(deductions.get("80D", 0), max_80d_self + max_80d_parents)
    
    # 80E - Education Loan Interest - No limit
    capped["80E"] = deductions.get("80E", 0)
    
    # 80G - Donations - Simplified
    capped["80G"] = deductions.get("80G", 0)
    
    # 80GG - Rent Paid (if not receiving HRA)
    capped["80GG"] = min(deductions.get("80GG", 0), limits.get("80GG", 60000))
    
    # 80TTA/80TTB - Savings Interest based on age
    if age >= 60:
        capped["80TTB"] = min(deductions.get("80TTB", 0), limits.get("80TTB", 50000))
        capped["80TTA"] = 0
    else:
        capped["80TTA"] = min(deductions.get("80TTA", 0), limits.get("80TTA", 10000))
        capped["80TTB"] = 0
    
    # 80U - Disability
    capped["80U"] = min(deductions.get("80U", 0), limits.get("80U_severe", 125000))
    
    # 80DD - Disabled Dependent
    capped["80DD"] = min(deductions.get("80DD", 0), limits.get("80DD_severe", 125000))
    
    # 80DDB - Medical Treatment based on age
    max_80ddb = limits.get("80DDB_senior", 100000) if age >= 60 else limits.get("80DDB", 40000)
    capped["80DDB"] = min(deductions.get("80DDB", 0), max_80ddb)
    
    # 80EE/80EEA - First Home Interest
    capped["80EE"] = min(deductions.get("80EE", 0), limits.get("80EE", 50000))
    capped["80EEA"] = min(deductions.get("80EEA", 0), limits.get("80EEA", 150000))
    
    # Section 24(b) - Home Loan Interest
    capped["24b_home_loan_interest"] = min(
        deductions.get("24b_home_loan_interest", 0), limits.get("24b", 200000)
    )
    
    # Standard Deduction and Professional Tax - under Section 16
    capped["Standard Deduction"] = min(deductions.get("Standard Deduction", 0), limits.get("Standard Deduction", 75000))
    capped["Professional Tax"] = min(deductions.get("Professional Tax", 0), 2500)
    
    return capped

def calculate_old_regime_tax(
    gross_income: float,
    deductions: Dict[str, float],
    age: int,
    rules: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate tax under old regime with comprehensive deductions"""
    
    print(f"\n📊 Calculating OLD REGIME tax...")
    print(f"   Gross Income: ₹{gross_income:,.0f}")
    
    # Apply deduction limits using rules
    capped_deductions = apply_deduction_limits(deductions, age, gross_income, rules)
    
    # Calculate total deductions
    total_deductions = sum(v for v in capped_deductions.values() if isinstance(v, (int, float)))
    
    # Cap total deductions at reasonable limit (shouldn't exceed income)
    total_deductions = min(total_deductions, gross_income)
    
    print(f"   Total Deductions: ₹{total_deductions:,.0f}")
    
    # Calculate taxable income
    taxable_income = max(0, gross_income - total_deductions)
    
    print(f"   Taxable Income: ₹{taxable_income:,.0f}")
    
    # Get age category and slabs
    age_category = get_age_category(age)
    
    # Try different slab formats in rules
    slabs = None
    try:
        slabs = rules["slabs"][age_category]["old_regime"]
    except KeyError:
        try:
            slabs = rules["income_tax_slabs"]["old_regime"]["general"]["slabs"]
        except KeyError:
            try:
                slabs = rules["income_tax_slabs"]["old_regime"][age_category.replace("individual_", "")]["slabs"]
            except KeyError:
                # Default old regime slabs for FY 2024-25
                slabs = [
                    {"min": 0, "max": 250000, "rate_percent": 0},
                    {"min": 250001, "max": 500000, "rate_percent": 5},
                    {"min": 500001, "max": 1000000, "rate_percent": 20},
                    {"min": 1000001, "max": None, "rate_percent": 30}
                ]
    
    # Calculate tax before rebate
    tax_before_rebate, breakdown = calculate_tax_by_slab_accurate(taxable_income, slabs)
    
    # Calculate rebate under section 87A
    rebate = 0.0
    try:
        rebate_config = rules["rebate_87A"]["old_regime"]
        if taxable_income <= rebate_config["max_total_income"]:
            rebate = min(tax_before_rebate, rebate_config["rebate_cap"])
    except KeyError:
        # Default: Rs. 12,500 rebate if income <= Rs. 5,00,000
        if taxable_income <= 500000:
            rebate = min(tax_before_rebate, 12500)
    
    # Tax after rebate
    tax_after_rebate = max(0, tax_before_rebate - rebate)
    
    # Calculate surcharge
    surcharge = calculate_surcharge(taxable_income, tax_after_rebate, rules, "old_regime")
    
    # Calculate cess (4% on tax + surcharge)
    try:
        cess_percent = rules["cess"]["health_and_education_cess_percent"]
    except KeyError:
        cess_percent = 4
    
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
    rules: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate tax under new regime (only limited deductions allowed)"""
    
    print(f"\n📊 Calculating NEW REGIME tax...")
    print(f"   Gross Income: ₹{gross_income:,.0f}")
    
    # New regime allows only limited deductions:
    # - Standard Deduction (amount based on FY from rules)
    # - 80CCD(2): Employer NPS contribution
    # - 80CCH: Agnipath Scheme
    # - Family Pension deduction under section 57(iia)
    
    # Get standard deduction from rules
    std_ded_limit = get_standard_deduction_from_rules(rules, "new_regime")
    standard_deduction = min(allowed_deductions.get("Standard Deduction", std_ded_limit), std_ded_limit)
    employer_nps = allowed_deductions.get("80CCD_2", 0)
    
    total_deductions = standard_deduction + employer_nps
    
    print(f"   Allowed Deductions: ₹{total_deductions:,.0f}")
    print(f"      Standard Deduction: ₹{standard_deduction:,.0f}")
    print(f"      Employer NPS (80CCD(2)): ₹{employer_nps:,.0f}")
    
    # Calculate taxable income
    taxable_income = max(0, gross_income - total_deductions)
    
    print(f"   Taxable Income: ₹{taxable_income:,.0f}")
    
    # New regime slabs for FY 2024-25 (same for all age groups)
    slabs = None
    try:
        slabs = rules["slabs"]["individual_below_60"]["new_regime_115BAC(1A)"]
    except KeyError:
        try:
            slabs = rules["income_tax_slabs"]["new_regime"]["general"]["slabs"]
        except KeyError:
            # Default new regime slabs for FY 2024-25
            slabs = [
                {"min": 0, "max": 300000, "rate_percent": 0},
                {"min": 300001, "max": 700000, "rate_percent": 5},
                {"min": 700001, "max": 1000000, "rate_percent": 10},
                {"min": 1000001, "max": 1200000, "rate_percent": 15},
                {"min": 1200001, "max": 1500000, "rate_percent": 20},
                {"min": 1500001, "max": None, "rate_percent": 30}
            ]
    
    # Calculate tax before rebate
    tax_before_rebate, breakdown = calculate_tax_by_slab_accurate(taxable_income, slabs)
    
    # Calculate rebate under section 87A (New Regime)
    # FY 2024-25: Rebate up to Rs. 25,000 if taxable income <= Rs. 7,00,000
    rebate = 0.0
    try:
        rebate_config = rules["rebate_87A"]["new_regime"]
        if taxable_income <= rebate_config["max_total_income"]:
            rebate = min(tax_before_rebate, rebate_config["rebate_cap"])
    except KeyError:
        # Default: 25000 rebate if income <= 700000
        if taxable_income <= 700000:
            rebate = min(tax_before_rebate, 25000)
    
    # Tax after rebate
    tax_after_rebate = max(0, tax_before_rebate - rebate)
    
    # Calculate surcharge (lower rates in new regime)
    surcharge = calculate_surcharge(taxable_income, tax_after_rebate, rules, "new_regime")
    
    # Calculate cess (4% on tax + surcharge)
    try:
        cess_percent = rules["cess"]["health_and_education_cess_percent"]
    except KeyError:
        cess_percent = 4
    
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


def calculate_surcharge(income: float, tax: float, rules: Dict[str, Any], regime: str) -> float:
    """Calculate surcharge based on income slabs with marginal relief"""
    
    try:
        if regime == "old_regime":
            thresholds = rules["surcharge_and_marginal_relief"]["surcharge_old_regime_thresholds"]
        else:
            thresholds = rules["surcharge_and_marginal_relief"]["surcharge_new_regime_thresholds"]
    except KeyError:
        # Default surcharge thresholds
        if regime == "old_regime":
            thresholds = [
                {"min_exclusive": 5000000, "rate_percent": 10},
                {"min_exclusive": 10000000, "rate_percent": 15},
                {"min_exclusive": 20000000, "rate_percent": 25},
                {"min_exclusive": 50000000, "rate_percent": 37}
            ]
        else:
            thresholds = [
                {"min_exclusive": 5000000, "rate_percent": 10},
                {"min_exclusive": 10000000, "rate_percent": 15},
                {"min_exclusive": 20000000, "rate_percent": 25}
            ]
    
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
    gross_income: float,
    has_business_income: bool = False,
    has_capital_gains: bool = False,
    has_foreign_assets: bool = False
) -> str:
    """Recommend appropriate ITR form"""
    
    # Simplified logic based on provided rules
    if has_foreign_assets or has_capital_gains:
        return "ITR-2"
    elif has_business_income:
        return "ITR-3"
    elif gross_income <= 5000000:
        return "ITR-1 (SAHAJ)"
    else:
        return "ITR-2"

def calculate_comprehensive_tax(
    user_data: Dict[str, Any],
    extracted_data: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """
    Comprehensive tax calculation combining data from all documents
    Uses accurate slab-based calculation for both regimes
    """
    
    print(f"\n{'='*60}")
    print(f"🧮 COMPREHENSIVE TAX CALCULATION")
    print(f"{'='*60}")
    
    financial_year = user_data.get("financial_year")
    dob = user_data.get("date_of_birth")
    age = calculate_age(dob) if dob else 30  # Default age if not provided
    
    print(f"Financial Year: {financial_year}")
    print(f"User Age: {age}")
    
    # Get tax rules for the financial year
    rules = get_tax_rules(db, financial_year)
    
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
    
    # Ensure minimum standard deduction for salaried
    if salary_income > 0 and old_regime_deductions.get("Standard Deduction", 0) == 0:
        # Apply standard deduction from rules
        std_ded = get_standard_deduction_from_rules(rules, "old_regime")
        old_regime_deductions["Standard Deduction"] = std_ded
        print(f"   Applied Standard Deduction from rules: ₹{std_ded:,}")
    
    print(f"Old Regime Deductions: {sum(v for v in old_regime_deductions.values() if isinstance(v, (int, float)))}")
    
    # === NEW REGIME DEDUCTIONS (Limited) ===
    # Standard Deduction amount from rules
    new_std_deduction = get_standard_deduction_from_rules(rules, "new_regime")
    
    new_regime_deductions = {
        "Standard Deduction": new_std_deduction,
        "80CCD_2": old_regime_deductions.get("80CCD_2", 0),  # Employer NPS
        "80CCH": old_regime_deductions.get("80CCH", 0),  # Agnipath
    }
    
    # === CALCULATE TAX UNDER BOTH REGIMES ===
    old_regime_result = calculate_old_regime_tax(
        gross_income, old_regime_deductions, age, rules
    )
    
    new_regime_result = calculate_new_regime_tax(
        gross_income, new_regime_deductions, age, rules
    )
    
    # === RECOMMEND REGIME ===
    recommended_regime, reason, savings = recommend_regime(
        old_regime_result, new_regime_result
    )
    
    print(f"\n📋 RECOMMENDATION: {recommended_regime}")
    print(f"   Tax Savings: ₹{savings:,.0f}")
    
    # === RECOMMEND ITR FORM ===
    has_capital_gains = extracted_data.get("has_capital_gains", False)
    has_business_income = extracted_data.get("has_business_income", False)
    has_foreign_assets = extracted_data.get("has_foreign_assets", False)
    
    # Check for capital gains and business income from amounts
    if extracted_data.get("capital_gains", 0) > 0:
        has_capital_gains = True
    if extracted_data.get("business_income", 0) > 0:
        has_business_income = True
    
    itr_form = recommend_itr_form(
        gross_income, 
        has_business_income, 
        has_capital_gains, 
        has_foreign_assets
    )
    
    print(f"   Recommended ITR Form: {itr_form}")
    
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
        "tax_savings": savings,
        "total_tds": total_tds,
        "advance_tax_paid": advance_tax,
        "self_assessment_tax": self_assessment_tax,
        "total_taxes_paid": total_taxes_paid,
        "tax_payable": tax_payable,
        "refund_amount": refund_amount
    }

