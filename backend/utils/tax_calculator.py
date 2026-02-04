from typing import Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from models import TaxRule
import json

def get_tax_rules(db: Session, financial_year: str) -> Dict[str, Any]:
    """Get tax rules for a specific financial year"""
    tax_rule = db.query(TaxRule).filter(
        TaxRule.financial_year == financial_year,
        TaxRule.is_active == True
    ).first()
    
    if not tax_rule:
        # Return default rules if not found
        # You should seed the database with the provided rules
        raise Exception(f"Tax rules for FY {financial_year} not found")
    
    return tax_rule.rules_json

def calculate_age(date_of_birth: datetime) -> int:
    """Calculate age from date of birth"""
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

def calculate_tax_by_slab(income: float, slabs: List[Dict[str, Any]]) -> float:
    """Calculate tax based on slab rates"""
    tax = 0.0
    
    for slab in slabs:
        if "upto" in slab:
            # First slab (0% tax)
            continue
        elif "over" in slab and "up_to" in slab:
            # Middle slabs
            lower = slab["over"]
            upper = slab["up_to"]
            
            if income > lower:
                taxable_in_slab = min(income, upper) - lower
                
                if "rate_percent" in slab:
                    tax += taxable_in_slab * slab["rate_percent"] / 100
                elif "formula" in slab:
                    # For new regime with formula
                    if income > upper:
                        # Use the fixed amount from formula
                        parts = slab["formula"].split("+")
                        base_tax = float(parts[0].strip())
                        tax = base_tax
        elif "over" in slab:
            # Last slab
            lower = slab["over"]
            if income > lower:
                taxable_in_slab = income - lower
                
                if "rate_percent" in slab:
                    tax += taxable_in_slab * slab["rate_percent"] / 100
                elif "formula" in slab:
                    parts = slab["formula"].split("+")
                    base_tax = float(parts[0].strip())
                    percent_str = parts[1].split("%")[0].strip()
                    percent = float(percent_str)
                    tax = base_tax + (taxable_in_slab * percent / 100)
    
    return tax

def calculate_old_regime_tax(
    gross_income: float,
    deductions: Dict[str, float],
    age: int,
    rules: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate tax under old regime"""
    
    # Calculate total deductions
    total_deductions = sum(deductions.values())
    
    # Calculate taxable income
    taxable_income = max(0, gross_income - total_deductions)
    
    # Get age category and slabs
    age_category = get_age_category(age)
    slabs = rules["slabs"][age_category]["old_regime"]
    
    # Calculate tax before rebate
    tax_before_rebate = calculate_tax_by_slab(taxable_income, slabs)
    
    # Calculate rebate under section 87A
    rebate = 0.0
    rebate_config = rules["rebate_87A"]["old_regime"]
    if taxable_income <= rebate_config["max_total_income"]:
        rebate = min(tax_before_rebate, rebate_config["rebate_cap"])
    
    # Tax after rebate
    tax_after_rebate = max(0, tax_before_rebate - rebate)
    
    # Calculate surcharge
    surcharge = calculate_surcharge(taxable_income, tax_after_rebate, rules, "old_regime")
    
    # Calculate cess (4% on tax + surcharge)
    cess_percent = rules["cess"]["health_and_education_cess_percent"]
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
    """Calculate tax under new regime (only specific deductions allowed)"""
    
    # Only certain deductions are allowed in new regime
    total_deductions = sum(allowed_deductions.values())
    
    # Calculate taxable income
    taxable_income = max(0, gross_income - total_deductions)
    
    # New regime slabs are same for all age groups
    slabs = rules["slabs"]["individual_below_60"]["new_regime_115BAC(1A)"]
    
    # Calculate tax before rebate
    tax_before_rebate = calculate_tax_by_slab(taxable_income, slabs)
    
    # Calculate rebate under section 87A
    rebate = 0.0
    rebate_config = rules["rebate_87A"]["new_regime"]
    if taxable_income <= rebate_config["max_total_income"]:
        rebate = min(tax_before_rebate, rebate_config["rebate_cap"])
    
    # Tax after rebate
    tax_after_rebate = max(0, tax_before_rebate - rebate)
    
    # Calculate surcharge
    surcharge = calculate_surcharge(taxable_income, tax_after_rebate, rules, "new_regime")
    
    # Calculate cess (4% on tax + surcharge)
    cess_percent = rules["cess"]["health_and_education_cess_percent"]
    cess = (tax_after_rebate + surcharge) * cess_percent / 100
    
    # Total tax
    total_tax = tax_after_rebate + surcharge + cess
    
    return {
        "deductions": allowed_deductions,
        "total_deductions": total_deductions,
        "taxable_income": taxable_income,
        "tax_before_rebate": tax_before_rebate,
        "rebate": rebate,
        "tax_after_rebate": tax_after_rebate,
        "surcharge": surcharge,
        "cess": cess,
        "total_tax": total_tax
    }

def calculate_surcharge(income: float, tax: float, rules: Dict[str, Any], regime: str) -> float:
    """Calculate surcharge based on income slabs"""
    
    if regime == "old_regime":
        thresholds = rules["surcharge_and_marginal_relief"]["surcharge_old_regime_thresholds"]
    else:
        thresholds = rules["surcharge_and_marginal_relief"]["surcharge_new_regime_thresholds"]
    
    surcharge_rate = 0
    for threshold in thresholds:
        if income > threshold["min_exclusive"]:
            surcharge_rate = threshold["rate_percent"]
    
    surcharge = tax * surcharge_rate / 100
    
    # Apply marginal relief if applicable
    # (Simplified - full implementation would check marginal relief conditions)
    
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
    """
    
    financial_year = user_data.get("financial_year")
    age = calculate_age(user_data.get("date_of_birth"))
    
    # Get tax rules for the financial year
    rules = get_tax_rules(db, financial_year)
    
    # Aggregate income from all sources
    gross_income = extracted_data.get("gross_total_income", 0)
    
    # Aggregate deductions (old regime)
    old_regime_deductions = extracted_data.get("old_regime_deductions", {})
    
    # New regime allowed deductions (very limited)
    new_regime_deductions = {
        "80CCD(2)": old_regime_deductions.get("80CCD(2)", 0),  # Employer NPS
        "80CCH": old_regime_deductions.get("80CCH", 0),  # Agnipath
    }
    
    # Calculate tax under both regimes
    old_regime_result = calculate_old_regime_tax(
        gross_income, old_regime_deductions, age, rules
    )
    
    new_regime_result = calculate_new_regime_tax(
        gross_income, new_regime_deductions, age, rules
    )
    
    # Recommend regime
    recommended_regime, reason, savings = recommend_regime(
        old_regime_result, new_regime_result
    )
    
    # Recommend ITR form
    itr_form = recommend_itr_form(gross_income)
    
    # Calculate final tax liability
    total_tds = extracted_data.get("total_tds", 0)
    
    if recommended_regime == "New Regime":
        final_tax = new_regime_result["total_tax"]
    else:
        final_tax = old_regime_result["total_tax"]
    
    tax_payable = max(0, final_tax - total_tds)
    refund_amount = max(0, total_tds - final_tax)
    
    return {
        "financial_year": financial_year,
        "assessment_year": rules.get("assessment_year"),
        "gross_total_income": gross_income,
        "old_regime": old_regime_result,
        "new_regime": new_regime_result,
        "recommended_regime": recommended_regime,
        "recommendation_reason": reason,
        "recommended_itr_form": itr_form,
        "tax_savings": savings,
        "total_tds": total_tds,
        "tax_payable": tax_payable,
        "refund_amount": refund_amount
    }

