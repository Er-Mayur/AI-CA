from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Document, TaxComputation, ActivityHistory, VerificationStatus
from schemas import TaxComputationResponse, TaxComputationDetail
from dependencies import get_current_user
from utils.tax_calculator import calculate_comprehensive_tax, calculate_age
from datetime import datetime

router = APIRouter()

@router.post("/calculate/{financial_year}", response_model=TaxComputationDetail)
def calculate_tax(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate tax for a financial year based on uploaded documents"""
    
    # Check if all required documents are uploaded and verified
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.financial_year == financial_year,
        Document.verification_status == VerificationStatus.VERIFIED
    ).all()
    
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verified documents found. Please upload and verify documents first."
        )
    
    # Aggregate extracted data from all documents
    aggregated_data = aggregate_document_data(documents)
    
    # Prepare user data
    user_data = {
        "financial_year": financial_year,
        "date_of_birth": current_user.date_of_birth,
        "pan_card": current_user.pan_card
    }
    
    # Calculate comprehensive tax
    try:
        tax_result = calculate_comprehensive_tax(user_data, aggregated_data, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating tax: {str(e)}"
        )
    
    # Check if computation already exists
    existing_computation = db.query(TaxComputation).filter(
        TaxComputation.user_id == current_user.id,
        TaxComputation.financial_year == financial_year
    ).first()
    
    if existing_computation:
        # Update existing computation
        computation = existing_computation
    else:
        # Create new computation
        computation = TaxComputation(
            user_id=current_user.id,
            financial_year=financial_year,
            assessment_year=tax_result["assessment_year"]
        )
        db.add(computation)
    
    # Update computation fields
    computation.gross_total_income = tax_result["gross_total_income"]
    computation.salary_income = aggregated_data.get("salary_income", 0)
    computation.house_property_income = aggregated_data.get("house_property_income", 0)
    computation.capital_gains = aggregated_data.get("capital_gains", 0)
    computation.other_income = aggregated_data.get("other_income", 0)
    
    # Old regime
    computation.old_regime_deductions = tax_result["old_regime"]["deductions"]
    computation.old_regime_total_deductions = tax_result["old_regime"]["total_deductions"]
    computation.old_regime_taxable_income = tax_result["old_regime"]["taxable_income"]
    computation.old_regime_tax_before_rebate = tax_result["old_regime"]["tax_before_rebate"]
    computation.old_regime_rebate = tax_result["old_regime"]["rebate"]
    computation.old_regime_tax_after_rebate = tax_result["old_regime"]["tax_after_rebate"]
    computation.old_regime_surcharge = tax_result["old_regime"]["surcharge"]
    computation.old_regime_cess = tax_result["old_regime"]["cess"]
    computation.old_regime_total_tax = tax_result["old_regime"]["total_tax"]
    
    # New regime
    computation.new_regime_deductions = tax_result["new_regime"]["deductions"]
    computation.new_regime_total_deductions = tax_result["new_regime"]["total_deductions"]
    computation.new_regime_taxable_income = tax_result["new_regime"]["taxable_income"]
    computation.new_regime_tax_before_rebate = tax_result["new_regime"]["tax_before_rebate"]
    computation.new_regime_rebate = tax_result["new_regime"]["rebate"]
    computation.new_regime_tax_after_rebate = tax_result["new_regime"]["tax_after_rebate"]
    computation.new_regime_surcharge = tax_result["new_regime"]["surcharge"]
    computation.new_regime_cess = tax_result["new_regime"]["cess"]
    computation.new_regime_total_tax = tax_result["new_regime"]["total_tax"]
    
    # Recommendation
    computation.recommended_regime = tax_result["recommended_regime"]
    computation.recommendation_reason = tax_result["recommendation_reason"]
    computation.recommended_itr_form = tax_result["recommended_itr_form"]
    computation.tax_savings = tax_result["tax_savings"]
    
    # TDS and final tax
    computation.total_tds = tax_result["total_tds"]
    computation.tax_payable = tax_result["tax_payable"]
    computation.refund_amount = tax_result["refund_amount"]
    
    computation.computed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(computation)
    
    # Log activity
    activity = ActivityHistory(
        user_id=current_user.id,
        financial_year=financial_year,
        activity_type="TAX_CALCULATION",
        description=f"Tax calculated for FY {financial_year}. Recommended regime: {tax_result['recommended_regime']}",
        activity_metadata={
            "computation_id": computation.id,
            "recommended_regime": tax_result["recommended_regime"],
            "tax_savings": tax_result["tax_savings"]
        }
    )
    db.add(activity)
    db.commit()
    
    return computation

@router.get("/computation/{financial_year}", response_model=TaxComputationDetail)
def get_tax_computation(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get existing tax computation for a financial year"""
    
    computation = db.query(TaxComputation).filter(
        TaxComputation.user_id == current_user.id,
        TaxComputation.financial_year == financial_year
    ).first()
    
    if not computation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax computation not found. Please calculate tax first."
        )
    
    return computation

def aggregate_document_data(documents):
    """
    Comprehensive aggregation of data from multiple tax documents
    Combines Form 16, Form 26AS, and AIS data intelligently
    """
    
    aggregated = {
        # Income Details
        "gross_total_income": 0,
        "salary_income": 0,
        "gross_salary": 0,
        "net_salary": 0,
        "house_property_income": 0,
        "capital_gains": 0,
        "capital_gains_short_term": 0,
        "capital_gains_long_term": 0,
        "other_income": 0,
        "interest_income": 0,
        "dividend_income": 0,
        "business_income": 0,
        
        # TDS Details
        "total_tds": 0,
        "tds_on_salary": 0,
        "advance_tax_paid": 0,
        "self_assessment_tax": 0,
        
        # Exemptions (Section 10, 16)
        "exemptions": {
            "hra_exemption": 0,
            "lta_exemption": 0,
            "standard_deduction": 0,
            "professional_tax": 0,
            "entertainment_allowance": 0,
            "total_exemptions": 0
        },
        
        # Chapter VI-A Deductions (Old Regime)
        "old_regime_deductions": {
            "80C": 0,
            "80CCC": 0,
            "80CCD_1": 0,
            "80CCD_1B": 0,
            "80CCD_2": 0,
            "80D": 0,
            "80DD": 0,
            "80DDB": 0,
            "80E": 0,
            "80EE": 0,
            "80EEA": 0,
            "80G": 0,
            "80GG": 0,
            "80TTA": 0,
            "80TTB": 0,
            "80U": 0,
            "24b_home_loan_interest": 0,
            "Standard Deduction": 0,
            "Professional Tax": 0,
        },
        
        # Tax computation details (from Form 16)
        "tax_on_total_income": 0,
        "rebate_87a": 0,
        "surcharge": 0,
        "cess": 0,
        "total_tax_liability": 0,
        "relief_89": 0,
        
        # Flags
        "has_capital_gains": False,
        "has_business_income": False,
        "has_foreign_assets": False,
    }
    
    for doc in documents:
        if not doc.extracted_data:
            continue
        
        data = doc.extracted_data
        doc_type_value = doc.doc_type.value if doc.doc_type else ""
        
        print(f"📊 Aggregating data from {doc_type_value}...")
        
        # === FORM 16 DATA ===
        if doc_type_value == "Form 16":
            # Salary Income - Use maximum (Form 16 is authoritative for salary)
            aggregated["salary_income"] = max(
                aggregated["salary_income"],
                _safe_float(data.get("gross_salary", 0)),
                _safe_float(data.get("salary_income", 0))
            )
            aggregated["gross_salary"] = max(
                aggregated["gross_salary"],
                _safe_float(data.get("gross_salary", 0))
            )
            aggregated["net_salary"] = max(
                aggregated["net_salary"],
                _safe_float(data.get("net_salary", 0))
            )
            
            # Gross Total Income
            aggregated["gross_total_income"] = max(
                aggregated["gross_total_income"],
                _safe_float(data.get("gross_total_income", 0)),
                _safe_float(data.get("total_income", 0))
            )
            
            # TDS
            aggregated["total_tds"] = max(
                aggregated["total_tds"],
                _safe_float(data.get("total_tds", 0)),
                _safe_float(data.get("total_tax_deducted", 0))
            )
            aggregated["tds_on_salary"] = max(
                aggregated["tds_on_salary"],
                _safe_float(data.get("tds_on_salary", 0))
            )
            
            # House Property Income/Loss
            hp_income = _safe_float(data.get("income_from_house_property", 0))
            if hp_income != 0:
                aggregated["house_property_income"] = hp_income
            
            # Other Income
            aggregated["other_income"] = max(
                aggregated["other_income"],
                _safe_float(data.get("income_from_other_sources", 0)),
                _safe_float(data.get("other_income", 0))
            )
            
            # === EXEMPTIONS (Section 10, 16) ===
            exemptions = data.get("exemptions", {})
            if isinstance(exemptions, dict):
                for key in ["hra_exemption", "lta_exemption", "standard_deduction", 
                           "professional_tax", "entertainment_allowance", "total_exemptions"]:
                    aggregated["exemptions"][key] = max(
                        aggregated["exemptions"].get(key, 0),
                        _safe_float(exemptions.get(key, 0))
                    )
            
            # Direct exemption fields (if not nested)
            if "standard_deduction" in data:
                aggregated["exemptions"]["standard_deduction"] = max(
                    aggregated["exemptions"]["standard_deduction"],
                    _safe_float(data.get("standard_deduction", 0))
                )
            if "professional_tax" in data:
                aggregated["exemptions"]["professional_tax"] = max(
                    aggregated["exemptions"]["professional_tax"],
                    _safe_float(data.get("professional_tax", 0))
                )
            
            # === CHAPTER VI-A DEDUCTIONS ===
            deductions = data.get("deductions", {})
            if isinstance(deductions, dict):
                for key in ["80C", "80CCC", "80CCD_1", "80CCD_1B", "80CCD_2", 
                           "80D", "80DD", "80DDB", "80E", "80EE", "80EEA",
                           "80G", "80GG", "80TTA", "80TTB", "80U", 
                           "24b_home_loan_interest", "total_deductions"]:
                    value = _safe_float(deductions.get(key, 0))
                    if value > 0:
                        aggregated["old_regime_deductions"][key] = max(
                            aggregated["old_regime_deductions"].get(key, 0),
                            value
                        )
                
                # Handle lowercase variations (from older extraction)
                key_mapping = {
                    "80c": "80C", "80ccc": "80CCC", "80ccd": "80CCD_1",
                    "80d": "80D", "80e": "80E", "80g": "80G"
                }
                for old_key, new_key in key_mapping.items():
                    value = _safe_float(deductions.get(old_key, 0))
                    if value > 0:
                        aggregated["old_regime_deductions"][new_key] = max(
                            aggregated["old_regime_deductions"].get(new_key, 0),
                            value
                        )
            
            # Add Standard Deduction and Professional Tax to deductions for old regime calc
            aggregated["old_regime_deductions"]["Standard Deduction"] = max(
                aggregated["old_regime_deductions"].get("Standard Deduction", 0),
                aggregated["exemptions"].get("standard_deduction", 0)
            )
            aggregated["old_regime_deductions"]["Professional Tax"] = max(
                aggregated["old_regime_deductions"].get("Professional Tax", 0),
                aggregated["exemptions"].get("professional_tax", 0)
            )
            
            # Tax computation details
            aggregated["tax_on_total_income"] = max(
                aggregated["tax_on_total_income"],
                _safe_float(data.get("tax_on_total_income", 0))
            )
            aggregated["rebate_87a"] = max(
                aggregated["rebate_87a"],
                _safe_float(data.get("rebate_87a", 0))
            )
            aggregated["surcharge"] = max(
                aggregated["surcharge"],
                _safe_float(data.get("surcharge", 0))
            )
            aggregated["cess"] = max(
                aggregated["cess"],
                _safe_float(data.get("cess", 0))
            )
            aggregated["relief_89"] = max(
                aggregated["relief_89"],
                _safe_float(data.get("relief_89", 0))
            )
        
        # === FORM 26AS DATA ===
        elif doc_type_value == "Form 26AS":
            # TDS from 26AS is authoritative
            aggregated["total_tds"] = max(
                aggregated["total_tds"],
                _safe_float(data.get("total_tds", 0))
            )
            aggregated["advance_tax_paid"] = max(
                aggregated["advance_tax_paid"],
                _safe_float(data.get("advance_tax_paid", 0))
            )
            aggregated["self_assessment_tax"] = max(
                aggregated["self_assessment_tax"],
                _safe_float(data.get("self_assessment_tax", 0))
            )
            
            # TDS details by section
            tds_details = data.get("tds_details", {})
            if isinstance(tds_details, dict):
                salary_tds = _safe_float(tds_details.get("salary_192", 0))
                if salary_tds > 0:
                    aggregated["tds_on_salary"] = max(
                        aggregated["tds_on_salary"], salary_tds
                    )
        
        # === AIS DATA ===
        elif doc_type_value == "AIS":
            # Income details
            aggregated["salary_income"] = max(
                aggregated["salary_income"],
                _safe_float(data.get("salary_income", 0)),
                _safe_float(data.get("salary", 0))
            )
            
            # Interest Income
            interest = _safe_float(data.get("interest_income", 0))
            if interest > 0:
                aggregated["interest_income"] = max(aggregated["interest_income"], interest)
                aggregated["other_income"] += interest  # Add to other income
            
            # Dividend Income
            dividend = _safe_float(data.get("dividend_income", 0))
            if dividend > 0:
                aggregated["dividend_income"] = max(aggregated["dividend_income"], dividend)
                aggregated["other_income"] += dividend
            
            # Capital Gains
            stcg = _safe_float(data.get("capital_gains_short_term", 0))
            ltcg = _safe_float(data.get("capital_gains_long_term", 0))
            if stcg > 0 or ltcg > 0:
                aggregated["capital_gains_short_term"] = max(aggregated["capital_gains_short_term"], stcg)
                aggregated["capital_gains_long_term"] = max(aggregated["capital_gains_long_term"], ltcg)
                aggregated["capital_gains"] = aggregated["capital_gains_short_term"] + aggregated["capital_gains_long_term"]
                aggregated["has_capital_gains"] = True
            
            # Business Income
            business = _safe_float(data.get("business_income", 0))
            if business > 0:
                aggregated["business_income"] = max(aggregated["business_income"], business)
                aggregated["has_business_income"] = True
            
            # Other Income
            other = _safe_float(data.get("other_income", 0))
            aggregated["other_income"] += other
            
            # TDS
            aggregated["total_tds"] = max(
                aggregated["total_tds"],
                _safe_float(data.get("total_tds", 0))
            )
    
    # === CALCULATE DERIVED VALUES ===
    
    # If salary_income is 0 but gross_salary exists, use gross_salary
    if aggregated["salary_income"] == 0 and aggregated["gross_salary"] > 0:
        aggregated["salary_income"] = aggregated["gross_salary"]
    
    # Calculate gross total income if not set
    if aggregated["gross_total_income"] == 0:
        aggregated["gross_total_income"] = (
            aggregated["salary_income"] +
            aggregated["house_property_income"] +
            aggregated["capital_gains"] +
            aggregated["other_income"] +
            aggregated["business_income"]
        )
    
    # Ensure standard deduction has reasonable defaults for salaried
    if aggregated["salary_income"] > 0 and aggregated["exemptions"]["standard_deduction"] == 0:
        # Default standard deduction (FY 2024-25: Rs. 75,000, earlier: Rs. 50,000)
        aggregated["exemptions"]["standard_deduction"] = 50000
        aggregated["old_regime_deductions"]["Standard Deduction"] = 50000
        print("   ℹ️ Applied default Standard Deduction: ₹50,000")
    
    print(f"✅ Aggregation complete:")
    print(f"   Gross Total Income: ₹{aggregated['gross_total_income']:,.0f}")
    print(f"   Salary Income: ₹{aggregated['salary_income']:,.0f}")
    print(f"   Total TDS: ₹{aggregated['total_tds']:,.0f}")
    print(f"   Deductions found: {sum(v for k, v in aggregated['old_regime_deductions'].items() if isinstance(v, (int, float)) and v > 0)}")
    
    return aggregated


def _safe_float(value) -> float:
    """Safely convert value to float"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            # Remove commas and currency symbols
            cleaned = value.replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').strip()
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0

