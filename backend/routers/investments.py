from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, TaxComputation, InvestmentSuggestion, ActivityHistory
from schemas import InvestmentSuggestionResponse
from dependencies import get_current_user
from utils.ollama_client import generate_investment_suggestions
from datetime import datetime

router = APIRouter()

@router.post("/suggest/{financial_year}", response_model=InvestmentSuggestionResponse)
async def get_investment_suggestions(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered investment suggestions to save tax"""
    
    # Get tax computation
    computation = db.query(TaxComputation).filter(
        TaxComputation.user_id == current_user.id,
        TaxComputation.financial_year == financial_year
    ).first()
    
    if not computation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax computation not found. Please calculate tax first."
        )
    
    # Generate suggestions using AI
    try:
        result = await generate_investment_suggestions(
            gross_income=computation.gross_total_income,
            current_deductions=computation.old_regime_deductions or {},
            taxable_income=computation.old_regime_taxable_income,
            financial_year=financial_year
        )
        
        # Check if suggestion already exists
        existing_suggestion = db.query(InvestmentSuggestion).filter(
            InvestmentSuggestion.user_id == current_user.id,
            InvestmentSuggestion.financial_year == financial_year
        ).first()
        
        if existing_suggestion:
            suggestion = existing_suggestion
            suggestion.suggestions = result["suggestions"]
            suggestion.potential_savings = result["total_potential_savings"]
        else:
            suggestion = InvestmentSuggestion(
                user_id=current_user.id,
                financial_year=financial_year,
                suggestions=result["suggestions"],
                potential_savings=result["total_potential_savings"]
            )
            db.add(suggestion)
        
        db.commit()
        db.refresh(suggestion)
        
        # Log activity
        activity = ActivityHistory(
            user_id=current_user.id,
            financial_year=financial_year,
            activity_type="INVESTMENT_SUGGESTION_GENERATED",
            description=f"Investment suggestions generated with potential savings of ₹{result['total_potential_savings']:,.2f}",
            activity_metadata={"suggestion_id": suggestion.id}
        )
        db.add(activity)
        db.commit()
        
        return suggestion
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating suggestions: {str(e)}"
        )

@router.get("/suggestions/{financial_year}", response_model=InvestmentSuggestionResponse)
def get_existing_suggestions(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get existing investment suggestions"""
    
    suggestion = db.query(InvestmentSuggestion).filter(
        InvestmentSuggestion.user_id == current_user.id,
        InvestmentSuggestion.financial_year == financial_year
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment suggestions not found. Generate them first."
        )
    
    return suggestion

