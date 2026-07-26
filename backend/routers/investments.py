from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, TaxComputation, InvestmentSuggestion, ActivityHistory
from schemas import InvestmentSuggestionResponse
from dependencies import get_current_user
from utils.ollama_client import generate_investment_suggestions
from datetime import datetime

router = APIRouter()


def _to_float(value) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _suggestion_is_stale(suggestion: InvestmentSuggestion, computation: TaxComputation) -> bool:
    """Check if saved suggestion inputs differ from current tax computation."""
    if not suggestion or not computation:
        return False

    gross_delta = abs(
        _to_float(suggestion.gross_income) - _to_float(computation.gross_total_income)
    )
    taxable_delta = abs(
        _to_float(suggestion.taxable_income) - _to_float(computation.old_regime_taxable_income)
    )

    # Ignore tiny float drift; refresh only when values materially changed.
    return gross_delta > 1.0 or taxable_delta > 1.0


async def _generate_and_store_suggestions(
    *,
    current_user: User,
    financial_year: str,
    computation: TaxComputation,
    db: Session,
    existing_suggestion: InvestmentSuggestion = None,
):
    """Generate investment suggestions and upsert them in DB."""
    result = await generate_investment_suggestions(
        gross_income=computation.gross_total_income,
        current_deductions=computation.old_regime_deductions or {},
        taxable_income=computation.old_regime_taxable_income,
        financial_year=financial_year,
        db=db,
    )

    suggestion = existing_suggestion
    if not suggestion:
        suggestion = db.query(InvestmentSuggestion).filter(
            InvestmentSuggestion.user_id == current_user.id,
            InvestmentSuggestion.financial_year == financial_year
        ).first()

    if suggestion:
        suggestion.suggestions = result["suggestions"]
        suggestion.potential_savings = result["total_potential_savings"]
        suggestion.deduction_summary = result.get("deduction_summary")
        suggestion.tax_rate = result.get("tax_rate")
        suggestion.gross_income = result.get("gross_income")
        suggestion.taxable_income = result.get("taxable_income")
    else:
        suggestion = InvestmentSuggestion(
            user_id=current_user.id,
            financial_year=financial_year,
            suggestions=result["suggestions"],
            potential_savings=result["total_potential_savings"],
            deduction_summary=result.get("deduction_summary"),
            tax_rate=result.get("tax_rate"),
            gross_income=result.get("gross_income"),
            taxable_income=result.get("taxable_income")
        )
        db.add(suggestion)

    db.commit()
    db.refresh(suggestion)
    return suggestion, result

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
    
    try:
        existing_suggestion = db.query(InvestmentSuggestion).filter(
            InvestmentSuggestion.user_id == current_user.id,
            InvestmentSuggestion.financial_year == financial_year
        ).first()
        suggestion, result = await _generate_and_store_suggestions(
            current_user=current_user,
            financial_year=financial_year,
            computation=computation,
            db=db,
            existing_suggestion=existing_suggestion,
        )
        
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
async def get_existing_suggestions(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get existing suggestions; auto-refresh if tax computation changed."""

    computation = db.query(TaxComputation).filter(
        TaxComputation.user_id == current_user.id,
        TaxComputation.financial_year == financial_year
    ).first()

    if not computation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax computation not found. Please calculate tax first."
        )
    
    suggestion = db.query(InvestmentSuggestion).filter(
        InvestmentSuggestion.user_id == current_user.id,
        InvestmentSuggestion.financial_year == financial_year
    ).first()

    # Auto-generate once if missing, so Benefits always reflects current numbers.
    if not suggestion:
        try:
            suggestion, _ = await _generate_and_store_suggestions(
                current_user=current_user,
                financial_year=financial_year,
                computation=computation,
                db=db,
            )
            return suggestion
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating suggestions: {str(e)}"
            )

    # Re-generate if tax inputs changed after a recalculation.
    if _suggestion_is_stale(suggestion, computation):
        try:
            suggestion, _ = await _generate_and_store_suggestions(
                current_user=current_user,
                financial_year=financial_year,
                computation=computation,
                db=db,
                existing_suggestion=suggestion,
            )
        except Exception as e:
            # Fall back to existing suggestion to avoid breaking page load.
            print(f"[WARN] Failed to refresh stale suggestions for FY {financial_year}: {e}")

    return suggestion

