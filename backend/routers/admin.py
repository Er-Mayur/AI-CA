"""
Admin Router - Tax Rules Management
Only accessible by admin users
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database import get_db
from models import TaxRule, User
from dependencies import get_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==========================================
# Pydantic Schemas
# ==========================================
class TaxRuleBase(BaseModel):
    financial_year: str = Field(..., example="2025-26", description="Financial Year (e.g., 2025-26)")
    assessment_year: str = Field(..., example="2026-27", description="Assessment Year (e.g., 2026-27)")
    rules_json: dict = Field(..., description="Complete tax rules JSON object")
    is_active: bool = Field(default=True, description="Whether this rule set is active")


class TaxRuleCreate(TaxRuleBase):
    pass


class TaxRuleUpdate(BaseModel):
    rules_json: Optional[dict] = None
    is_active: Optional[bool] = None


class TaxRuleResponse(TaxRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaxRuleSummary(BaseModel):
    """Summary view without full rules JSON"""
    id: int
    financial_year: str
    assessment_year: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    has_slabs: bool
    has_deductions: bool
    cess_percent: Optional[float] = None
    
    class Config:
        from_attributes = True


class TaxRuleTemplate(BaseModel):
    """Template structure for new FY rules"""
    template: dict
    instructions: List[str]


# ==========================================
# API Endpoints
# ==========================================

@router.get("/tax-rules", response_model=List[TaxRuleSummary])
def list_tax_rules(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all tax rules (summary view)"""
    rules = db.query(TaxRule).order_by(TaxRule.financial_year.desc()).all()
    
    summaries = []
    for rule in rules:
        rules_json = rule.rules_json or {}
        summaries.append(TaxRuleSummary(
            id=rule.id,
            financial_year=rule.financial_year,
            assessment_year=rule.assessment_year,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            has_slabs="slabs" in rules_json or "income_tax_slabs" in rules_json,
            has_deductions="deductions" in rules_json or "common_deductions_exemptions" in rules_json,
            cess_percent=rules_json.get("cess", {}).get("health_and_education_cess_percent")
        ))
    
    return summaries


@router.get("/tax-rules/{financial_year}", response_model=TaxRuleResponse)
def get_tax_rule(
    financial_year: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get complete tax rules for a specific financial year"""
    rule = db.query(TaxRule).filter(TaxRule.financial_year == financial_year).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax rules not found for FY {financial_year}"
        )
    
    return rule


@router.post("/tax-rules", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
def create_tax_rule(
    tax_rule: TaxRuleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Create new tax rules for a financial year"""
    # Check if rules already exist for this FY
    existing = db.query(TaxRule).filter(
        TaxRule.financial_year == tax_rule.financial_year
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tax rules already exist for FY {tax_rule.financial_year}. Use PUT to update."
        )
    
    # Validate required fields in rules_json
    validation_errors = _validate_rules_json(tax_rule.rules_json)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Invalid rules JSON structure", "errors": validation_errors}
        )
    
    # Ensure financial_year is set in rules_json
    rules_json = tax_rule.rules_json.copy()
    rules_json["financial_year"] = tax_rule.financial_year
    rules_json["assessment_year"] = tax_rule.assessment_year
    
    new_rule = TaxRule(
        financial_year=tax_rule.financial_year,
        assessment_year=tax_rule.assessment_year,
        rules_json=rules_json,
        is_active=tax_rule.is_active
    )
    
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    return new_rule


@router.put("/tax-rules/{financial_year}", response_model=TaxRuleResponse)
def update_tax_rule(
    financial_year: str,
    update_data: TaxRuleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update existing tax rules for a financial year"""
    rule = db.query(TaxRule).filter(TaxRule.financial_year == financial_year).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax rules not found for FY {financial_year}"
        )
    
    if update_data.rules_json is not None:
        # Validate rules JSON
        validation_errors = _validate_rules_json(update_data.rules_json)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Invalid rules JSON structure", "errors": validation_errors}
            )
        
        # Ensure financial_year is preserved
        rules_json = update_data.rules_json.copy()
        rules_json["financial_year"] = financial_year
        rules_json["assessment_year"] = rule.assessment_year
        rule.rules_json = rules_json
    
    if update_data.is_active is not None:
        rule.is_active = update_data.is_active
    
    rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/tax-rules/{financial_year}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tax_rule(
    financial_year: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Delete tax rules for a financial year"""
    rule = db.query(TaxRule).filter(TaxRule.financial_year == financial_year).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tax rules not found for FY {financial_year}"
        )
    
    db.delete(rule)
    db.commit()
    
    return None


@router.get("/tax-rules-template", response_model=TaxRuleTemplate)
def get_tax_rule_template(
    admin: User = Depends(get_admin_user)
):
    """Get a template structure for creating new tax rules"""
    template = {
        "schema_version": "1.0.0",
        "assessment_year": "20XX-XX",
        "financial_year": "20XX-XX",
        "source": {
            "title": "Salaried Individuals for AY 20XX-XX | Income Tax Department",
            "page_url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1#taxdeductions",
            "page_last_reviewed_dates": ["YYYY-MM-DD"],
            "note": "Copy rules from official government tax website"
        },
        "cess": {
            "health_and_education_cess_percent": 4
        },
        "rebate_87A": {
            "old_regime": {
                "max_total_income": 500000,
                "rebate_cap": 12500,
                "resident_only": True,
                "nr_not_eligible": True
            },
            "new_regime": {
                "max_total_income": 700000,
                "rebate_cap": 25000,
                "resident_only": True,
                "nr_not_eligible": True
            }
        },
        "surcharge_and_marginal_relief": {
            "surcharge_old_regime_thresholds": [
                {"min_exclusive": 5000000, "rate_percent": 10},
                {"min_exclusive": 10000000, "rate_percent": 15},
                {"min_exclusive": 20000000, "rate_percent": 25},
                {"min_exclusive": 50000000, "rate_percent": 37}
            ],
            "surcharge_new_regime_thresholds": [
                {"min_exclusive": 5000000, "rate_percent": 10},
                {"min_exclusive": 10000000, "rate_percent": 15},
                {"min_exclusive": 20000000, "rate_percent": 25}
            ],
            "marginal_relief_applicable": True
        },
        "slabs": {
            "individual_below_60": {
                "old_regime": [
                    {"min": 0, "max": 250000, "rate_percent": 0},
                    {"min": 250001, "max": 500000, "rate_percent": 5},
                    {"min": 500001, "max": 1000000, "rate_percent": 20},
                    {"min": 1000001, "max": None, "rate_percent": 30}
                ],
                "new_regime_115BAC(1A)": [
                    {"min": 0, "max": 300000, "rate_percent": 0},
                    {"min": 300001, "max": 700000, "rate_percent": 5},
                    {"min": 700001, "max": 1000000, "rate_percent": 10},
                    {"min": 1000001, "max": 1200000, "rate_percent": 15},
                    {"min": 1200001, "max": 1500000, "rate_percent": 20},
                    {"min": 1500001, "max": None, "rate_percent": 30}
                ]
            },
            "individual_60_to_79": {
                "old_regime": [
                    {"min": 0, "max": 300000, "rate_percent": 0},
                    {"min": 300001, "max": 500000, "rate_percent": 5},
                    {"min": 500001, "max": 1000000, "rate_percent": 20},
                    {"min": 1000001, "max": None, "rate_percent": 30}
                ],
                "new_regime_115BAC(1A)": "Same as individual_below_60"
            },
            "individual_80_and_above": {
                "old_regime": [
                    {"min": 0, "max": 500000, "rate_percent": 0},
                    {"min": 500001, "max": 1000000, "rate_percent": 20},
                    {"min": 1000001, "max": None, "rate_percent": 30}
                ],
                "new_regime_115BAC(1A)": "Same as individual_below_60"
            }
        },
        "deductions": {
            "old_regime_chapter_VIA_and_others": {
                "section_80C_80CCC_80CCD1": {
                    "combined_limit": 150000,
                    "instruments": ["ELSS", "PPF", "EPF", "LIC", "NSC", "Tax Saver FD", "Tuition Fees", "Home Loan Principal"]
                },
                "section_80CCD1B": {
                    "additional_limit": 50000,
                    "notes": "Additional NPS contribution"
                },
                "section_80D_health_insurance": {
                    "self_family": {"limit": 25000, "senior_citizen_limit": 50000, "preventive_checkup_included_limit": 5000},
                    "parents": {"limit": 25000, "senior_citizen_limit": 50000}
                },
                "section_80TTA_savings_interest_non_senior": {"limit": 10000},
                "section_80TTB_deposit_interest_senior": {"limit": 50000}
            },
            "new_regime_115BAC(1A)_allowed": {
                "section_80CCD_2_employer_nps": {
                    "limit": [
                        {"employer_type": "Central/State Government", "percent_of_salary": 14},
                        {"employer_type": "PSU/Others", "percent_of_salary": 10}
                    ]
                }
            }
        }
    }
    
    instructions = [
        "1. Visit https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1#taxdeductions",
        "2. Copy the official tax rules for the new Assessment Year",
        "3. Update 'financial_year' and 'assessment_year' fields",
        "4. Update 'source.page_last_reviewed_dates' with today's date",
        "5. Update 'rebate_87A' limits if changed in budget",
        "6. Update 'slabs' if tax brackets changed",
        "7. Update 'deductions' limits (80C, 80D, etc.) if changed",
        "8. Update 'surcharge_and_marginal_relief' thresholds if changed",
        "9. Verify 'cess' percentage (currently 4%)",
        "10. After creating, test with sample tax calculations"
    ]
    
    return TaxRuleTemplate(template=template, instructions=instructions)


@router.post("/tax-rules/{financial_year}/duplicate")
def duplicate_tax_rule(
    financial_year: str,
    new_financial_year: str,
    new_assessment_year: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Duplicate existing tax rules to create a new FY (as a starting point)"""
    # Get source rules
    source = db.query(TaxRule).filter(TaxRule.financial_year == financial_year).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source tax rules not found for FY {financial_year}"
        )
    
    # Check if target already exists
    existing = db.query(TaxRule).filter(TaxRule.financial_year == new_financial_year).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tax rules already exist for FY {new_financial_year}"
        )
    
    # Clone rules JSON and update FY/AY
    new_rules = source.rules_json.copy()
    new_rules["financial_year"] = new_financial_year
    new_rules["assessment_year"] = new_assessment_year
    new_rules["source"]["note"] = f"Duplicated from FY {financial_year} - PLEASE UPDATE WITH OFFICIAL VALUES"
    
    # Create new rule
    new_rule = TaxRule(
        financial_year=new_financial_year,
        assessment_year=new_assessment_year,
        rules_json=new_rules,
        is_active=False  # Set inactive until verified
    )
    
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    return {
        "message": f"Tax rules duplicated from FY {financial_year} to FY {new_financial_year}",
        "id": new_rule.id,
        "financial_year": new_rule.financial_year,
        "is_active": new_rule.is_active,
        "note": "Rules are created as INACTIVE. Update with official values and activate."
    }


@router.get("/check-admin")
def check_admin_status(
    admin: User = Depends(get_admin_user)
):
    """Check if current user has admin access"""
    return {
        "is_admin": True,
        "user_id": admin.id,
        "email": admin.email
    }


# ==========================================
# Helper Functions
# ==========================================

def _validate_rules_json(rules: dict) -> List[str]:
    """Validate that rules JSON has required structure"""
    errors = []
    
    # Required top-level keys
    required_keys = ["cess", "rebate_87A", "surcharge_and_marginal_relief"]
    for key in required_keys:
        if key not in rules:
            errors.append(f"Missing required key: '{key}'")
    
    # Must have either slabs or income_tax_slabs
    if "slabs" not in rules and "income_tax_slabs" not in rules:
        errors.append("Missing tax slabs: must have either 'slabs' or 'income_tax_slabs' key")
    
    # Must have either deductions or common_deductions_exemptions
    if "deductions" not in rules and "common_deductions_exemptions" not in rules:
        errors.append("Missing deductions: must have either 'deductions' or 'common_deductions_exemptions' key")
    
    # Validate cess structure
    if "cess" in rules:
        if "health_and_education_cess_percent" not in rules["cess"]:
            errors.append("Missing 'health_and_education_cess_percent' in cess")
    
    # Validate rebate structure
    if "rebate_87A" in rules:
        rebate = rules["rebate_87A"]
        for regime in ["old_regime", "new_regime"]:
            if regime not in rebate:
                errors.append(f"Missing '{regime}' in rebate_87A")
            elif not isinstance(rebate[regime], dict):
                errors.append(f"rebate_87A.{regime} must be an object")
    
    return errors
