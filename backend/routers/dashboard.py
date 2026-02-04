from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Document, TaxComputation, ActivityHistory, VerificationStatus
from schemas import DashboardStats, ActivityHistoryResponse
from dependencies import get_current_user
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/stats/{financial_year}", response_model=DashboardStats)
def get_dashboard_stats(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for a financial year"""
    
    # Count documents
    total_documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.financial_year == financial_year
    ).count()
    
    verified_documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.financial_year == financial_year,
        Document.verification_status == VerificationStatus.VERIFIED
    ).count()
    
    # Get tax computation
    computation = db.query(TaxComputation).filter(
        TaxComputation.user_id == current_user.id,
        TaxComputation.financial_year == financial_year
    ).first()
    
    if computation:
        tax_computed = True
        gross_income = computation.gross_total_income
        
        # Use recommended regime tax
        if computation.recommended_regime == "New Regime":
            total_tax = computation.new_regime_total_tax
        else:
            total_tax = computation.old_regime_total_tax
        
        tds_deducted = computation.total_tds
        
        if computation.tax_payable > 0:
            net_payable_refund = -computation.tax_payable  # Negative means payable
        else:
            net_payable_refund = computation.refund_amount  # Positive means refund
        
        recommended_regime = computation.recommended_regime
    else:
        tax_computed = False
        gross_income = 0
        total_tax = 0
        tds_deducted = 0
        net_payable_refund = 0
        recommended_regime = None
    
    return DashboardStats(
        financial_year=financial_year,
        documents_uploaded=total_documents,
        documents_verified=verified_documents,
        tax_computed=tax_computed,
        gross_income=gross_income,
        total_tax=total_tax,
        tds_deducted=tds_deducted,
        net_payable_refund=net_payable_refund,
        recommended_regime=recommended_regime
    )

@router.get("/activities/{financial_year}", response_model=List[ActivityHistoryResponse])
def get_activities(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity history for a financial year"""
    
    activities = db.query(ActivityHistory).filter(
        ActivityHistory.user_id == current_user.id,
        ActivityHistory.financial_year == financial_year
    ).order_by(ActivityHistory.timestamp.desc()).limit(50).all()
    
    return activities

@router.get("/current-year")
def get_current_financial_year():
    """Get current financial year"""
    now = datetime.now()
    
    # Indian financial year runs from April 1 to March 31
    if now.month >= 4:
        fy_start_year = now.year
        fy_end_year = now.year + 1
    else:
        fy_start_year = now.year - 1
        fy_end_year = now.year
    
    financial_year = f"{fy_start_year}-{str(fy_end_year)[-2:]}"
    assessment_year = f"{fy_end_year}-{str(fy_end_year + 1)[-2:]}"
    
    return {
        "financial_year": financial_year,
        "assessment_year": assessment_year
    }

