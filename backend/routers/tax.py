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
    """Aggregate data from multiple documents"""
    
    aggregated = {
        "gross_total_income": 0,
        "salary_income": 0,
        "house_property_income": 0,
        "capital_gains": 0,
        "other_income": 0,
        "total_tds": 0,
        "old_regime_deductions": {}
    }
    
    for doc in documents:
        if not doc.extracted_data:
            continue
        
        data = doc.extracted_data
        
        # Aggregate income (use maximum or sum based on document type)
        # Form 16 typically has the most complete salary info
        if doc.doc_type.value == "Form 16":
            aggregated["salary_income"] = max(
                aggregated["salary_income"],
                data.get("gross_salary", 0)
            )
            aggregated["gross_total_income"] = max(
                aggregated["gross_total_income"],
                data.get("total_income", 0)
            )
            aggregated["total_tds"] = max(
                aggregated["total_tds"],
                data.get("total_tds", 0)
            )
            
            # Deductions from Form 16
            if "deductions" in data:
                for key, value in data["deductions"].items():
                    aggregated["old_regime_deductions"][key] = aggregated["old_regime_deductions"].get(key, 0) + value
            
            # Add Standard Deduction and Professional Tax
            if data.get("standard_deduction"):
                aggregated["old_regime_deductions"]["Standard Deduction"] = (
                    aggregated["old_regime_deductions"].get("Standard Deduction", 0) + 
                    data.get("standard_deduction", 0)
                )
            
            if data.get("professional_tax"):
                aggregated["old_regime_deductions"]["Professional Tax"] = (
                    aggregated["old_regime_deductions"].get("Professional Tax", 0) + 
                    data.get("professional_tax", 0)
                )
        
        # Form 26AS has TDS details
        elif doc.doc_type.value == "Form 26AS":
            aggregated["total_tds"] = max(
                aggregated["total_tds"],
                data.get("total_tds", 0)
            )
        
        # AIS has comprehensive income details
        elif doc.doc_type.value == "AIS":
            aggregated["salary_income"] = max(
                aggregated["salary_income"],
                data.get("salary", 0),
                data.get("salary_income", 0)
            )
            aggregated["other_income"] += data.get("interest_income", 0)
            aggregated["other_income"] += data.get("dividend_income", 0)
            aggregated["other_income"] += data.get("other_income", 0)
            aggregated["capital_gains"] += data.get("capital_gains", 0)
            aggregated["business_income"] = max(
                aggregated.get("business_income", 0),
                data.get("business_income", 0)
            )
    
    # Calculate gross total income if not set
    if aggregated["gross_total_income"] == 0:
        aggregated["gross_total_income"] = (
            aggregated["salary_income"] +
            aggregated["house_property_income"] +
            aggregated["capital_gains"] +
            aggregated["other_income"]
        )
    
    return aggregated

