from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, Document, TaxComputation, ActivityHistory, VerificationStatus
from schemas import TaxComputationResponse, TaxComputationDetail
from dependencies import get_current_user
from utils.tax_calculator import calculate_comprehensive_tax, calculate_age
try:
    from utils.helper_report_generator import generate_helper_report
except Exception:
    generate_helper_report = None
from utils.rules_service import RulesService, TaxRulesNotFoundError
from utils.ollama_client import detect_itr_form_with_ai
from utils.pdf_processor import extract_text_from_pdf_advanced
from utils.smart_extractor import extract_with_smart_extractor
import os
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

    # Recover stale extraction rows (older uploads may contain mostly zeros due previous OCR parser behavior).
    refreshed_any = False
    for doc in documents:
        data = doc.extracted_data or {}
        has_key_financial_values = any(
            _safe_float(data.get(key, 0)) > 0
            for key in [
                "gross_total_income",
                "gross_salary",
                "salary_income",
                "total_income",
                "total_tds",
            ]
        )

        if has_key_financial_values:
            continue

        if not doc.file_path or not os.path.exists(doc.file_path):
            continue

        try:
            print(f"🔄 Re-extracting stale data for {doc.doc_type.value} (document_id={doc.id})...")
            text = extract_text_from_pdf_advanced(doc.file_path)
            recovered = extract_with_smart_extractor(
                text=text,
                user_name=current_user.name,
                user_pan=current_user.pan_card,
                expected_fy=financial_year,
            )
            recovered["_recovered_during_tax_calc"] = True
            doc.extracted_data = recovered
            refreshed_any = True
        except Exception as e:
            print(f"⚠️ Failed to re-extract stale document {doc.id}: {e}")

    if refreshed_any:
        db.commit()
        for doc in documents:
            db.refresh(doc)
    
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


@router.post("/detect-itr-form/{financial_year}")
async def detect_itr_form(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect the correct ITR form type using AI.
    
    Analyzes uploaded documents (Form 16, AIS, Form 26AS) to determine
    the appropriate ITR form based on Income Tax Act rules.
    
    Returns:
        - itr_form: Recommended ITR form (ITR-1, ITR-2, ITR-3, ITR-4)
        - reason: Detailed explanation
        - detected_income_heads: Income breakdown
        - eligibility_indicators: Factors that determined the form
    """
    
    # Get all verified documents
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
    
    # Prepare user data for detection
    user_data = {
        "financial_year": financial_year,
        "is_resident": True,  # Default assumption
        "pan_card": current_user.pan_card
    }
    
    # Call AI to detect ITR form
    try:
        result = await detect_itr_form_with_ai(
            aggregated_data=aggregated_data,
            user_data=user_data,
            financial_year=financial_year
        )
        
        # Update computation with detected ITR form if it exists
        computation = db.query(TaxComputation).filter(
            TaxComputation.user_id == current_user.id,
            TaxComputation.financial_year == financial_year
        ).first()
        
        if computation:
            computation.recommended_itr_form = result["itr_form"]
            db.commit()
        
        # Log activity
        activity = ActivityHistory(
            user_id=current_user.id,
            financial_year=financial_year,
            activity_type="ITR_FORM_DETECTED",
            description=f"AI detected ITR form: {result['itr_form']} - {result.get('detection_method', 'ai')}",
            activity_metadata={
                "itr_form": result["itr_form"],
                "confidence": result.get("confidence", "unknown"),
                "detection_method": result.get("detection_method", "ai"),
                "key_factors": result.get("key_factors", [])
            }
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "financial_year": financial_year,
            "itr_form": result["itr_form"],
            "reason": result["reason"],
            "detected_income_heads": result.get("detected_income_heads", {}),
            "eligibility_indicators": result.get("eligibility_indicators", {}),
            "key_factors": result.get("key_factors", []),
            "warnings": result.get("warnings", []),
            "confidence": result.get("confidence", "medium"),
            "detection_method": result.get("detection_method", "ai")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting ITR form: {str(e)}"
        )


def aggregate_document_data(documents):
    """
    Comprehensive aggregation of data from multiple tax documents
    Combines Form 16, Form 26AS, and AIS data intelligently
    
    Extracts signals for ITR form type detection:
    - Income from all sources
    - TDS section codes
    - Eligibility indicators (foreign assets, director status, etc.)
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
        "capital_gains_ltcg_112a": 0,  # LTCG under section 112A (equity)
        "other_income": 0,
        "interest_income": 0,
        "dividend_income": 0,
        "business_income": 0,
        "professional_income": 0,
        "agricultural_income": 0,
        "crypto_income": 0,
        "rental_income": 0,
        
        # TDS Details
        "total_tds": 0,
        "tds_on_salary": 0,
        "advance_tax_paid": 0,
        "self_assessment_tax": 0,
        
        # TDS Section codes (for ITR form detection)
        "tds_sections": [],
        "tds_details": {},
        
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
        
        # === ITR FORM ELIGIBILITY FLAGS ===
        "has_capital_gains": False,
        "has_business_income": False,
        "has_foreign_assets": False,
        "has_foreign_income": False,
        "is_director_in_company": False,
        "has_unlisted_equity": False,
        "is_resident": True,
        "num_house_properties": 1,
        "multiple_house_properties": False,
        
        # Presumptive taxation flags
        "has_presumptive_income_44ad": False,
        "has_presumptive_income_44ada": False,
        "has_presumptive_income_44ae": False,
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
            
            # TDS details by section - Extract section codes for ITR form detection
            tds_details = data.get("tds_details", {})
            if isinstance(tds_details, dict):
                # Merge TDS details
                for section_key, amount in tds_details.items():
                    if section_key not in aggregated["tds_details"]:
                        aggregated["tds_details"][section_key] = 0
                    aggregated["tds_details"][section_key] = max(
                        aggregated["tds_details"][section_key],
                        _safe_float(amount)
                    )
                    
                    # Extract section code and add to list
                    # Handle various formats: "salary_192", "192", "section_192"
                    import re
                    section_match = re.search(r'(\d+[A-Z]*)', str(section_key).upper())
                    if section_match:
                        section_code = section_match.group(1)
                        if section_code not in aggregated["tds_sections"]:
                            aggregated["tds_sections"].append(section_code)
                
                # Salary TDS (192)
                salary_tds = _safe_float(tds_details.get("salary_192", 0))
                if salary_tds == 0:
                    salary_tds = _safe_float(tds_details.get("192", 0))
                if salary_tds > 0:
                    aggregated["tds_on_salary"] = max(
                        aggregated["tds_on_salary"], salary_tds
                    )
                    if "192" not in aggregated["tds_sections"]:
                        aggregated["tds_sections"].append("192")
                
                # Professional income detection (194J)
                prof_tds = _safe_float(tds_details.get("194J", 0)) + _safe_float(tds_details.get("professional_194J", 0))
                if prof_tds > 0:
                    if "194J" not in aggregated["tds_sections"]:
                        aggregated["tds_sections"].append("194J")
                    # Estimate professional income from TDS (assuming 10% TDS rate)
                    estimated_prof_income = prof_tds / 0.1
                    aggregated["professional_income"] = max(
                        aggregated["professional_income"],
                        estimated_prof_income
                    )
                    aggregated["has_business_income"] = True
                
                # Contractor income detection (194C)
                contractor_tds = _safe_float(tds_details.get("194C", 0)) + _safe_float(tds_details.get("contractor_194C", 0))
                if contractor_tds > 0:
                    if "194C" not in aggregated["tds_sections"]:
                        aggregated["tds_sections"].append("194C")
                    aggregated["has_business_income"] = True
                
                # Commission income detection (194H)
                commission_tds = _safe_float(tds_details.get("194H", 0)) + _safe_float(tds_details.get("commission_194H", 0))
                if commission_tds > 0:
                    if "194H" not in aggregated["tds_sections"]:
                        aggregated["tds_sections"].append("194H")
                    aggregated["has_business_income"] = True
                
                # Property sale detection (194IA)
                property_tds = _safe_float(tds_details.get("194IA", 0)) + _safe_float(tds_details.get("property_sale_194IA", 0))
                if property_tds > 0:
                    if "194IA" not in aggregated["tds_sections"]:
                        aggregated["tds_sections"].append("194IA")
                    aggregated["has_capital_gains"] = True
                
                # Crypto detection (194S)
                crypto_tds = _safe_float(tds_details.get("194S", 0)) + _safe_float(tds_details.get("crypto_194S", 0))
                if crypto_tds > 0:
                    if "194S" not in aggregated["tds_sections"]:
                        aggregated["tds_sections"].append("194S")
                    # Estimate crypto income (1% TDS rate)
                    estimated_crypto = crypto_tds / 0.01
                    aggregated["crypto_income"] = max(aggregated["crypto_income"], estimated_crypto)
                    aggregated["has_capital_gains"] = True
            
            # Also check for TDS sections directly in the extracted data
            tds_sections_raw = data.get("tds_sections", [])
            if isinstance(tds_sections_raw, list):
                for section in tds_sections_raw:
                    section_str = str(section).upper()
                    if section_str not in aggregated["tds_sections"]:
                        aggregated["tds_sections"].append(section_str)
        
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
            
            # LTCG under section 112A (equity/mutual funds)
            ltcg_112a = _safe_float(data.get("capital_gains_ltcg_112a", 0))
            if ltcg_112a == 0:
                ltcg_112a = _safe_float(data.get("equity_ltcg", 0))
            if ltcg_112a > 0:
                aggregated["capital_gains_ltcg_112a"] = max(aggregated["capital_gains_ltcg_112a"], ltcg_112a)
            
            # Crypto/Virtual Digital Assets
            crypto = _safe_float(data.get("crypto_income", 0))
            if crypto == 0:
                crypto = _safe_float(data.get("vda_income", 0))
            if crypto > 0:
                aggregated["crypto_income"] = max(aggregated["crypto_income"], crypto)
                aggregated["has_capital_gains"] = True
            
            # Business Income
            business = _safe_float(data.get("business_income", 0))
            if business > 0:
                aggregated["business_income"] = max(aggregated["business_income"], business)
                aggregated["has_business_income"] = True
            
            # Professional Income
            professional = _safe_float(data.get("professional_income", 0))
            if professional > 0:
                aggregated["professional_income"] = max(aggregated["professional_income"], professional)
                aggregated["has_business_income"] = True
            
            # Foreign assets/income detection
            if data.get("foreign_assets") or data.get("has_foreign_assets"):
                aggregated["has_foreign_assets"] = True
            if data.get("foreign_income") or data.get("has_foreign_income"):
                aggregated["has_foreign_income"] = True
            foreign_income_value = _safe_float(data.get("foreign_income_value", 0))
            if foreign_income_value > 0:
                aggregated["has_foreign_income"] = True
            
            # Director status
            if data.get("is_director") or data.get("is_director_in_company"):
                aggregated["is_director_in_company"] = True
            
            # Unlisted equity
            if data.get("unlisted_equity") or data.get("has_unlisted_equity"):
                aggregated["has_unlisted_equity"] = True
            
            # House property count
            hp_count = data.get("num_house_properties", 0)
            if hp_count > 1:
                aggregated["num_house_properties"] = max(aggregated["num_house_properties"], hp_count)
                aggregated["multiple_house_properties"] = True
            if data.get("multiple_house_properties"):
                aggregated["multiple_house_properties"] = True
                aggregated["num_house_properties"] = max(2, aggregated["num_house_properties"])
            
            # Agricultural income
            agri = _safe_float(data.get("agricultural_income", 0))
            if agri > 0:
                aggregated["agricultural_income"] = max(aggregated["agricultural_income"], agri)
            
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
            aggregated["business_income"] +
            aggregated["professional_income"]
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
    
    # Log ITR form detection signals
    if aggregated["tds_sections"]:
        print(f"   TDS Sections found: {aggregated['tds_sections']}")
    if aggregated["has_capital_gains"]:
        print(f"   Capital Gains: ₹{aggregated['capital_gains']:,.0f}")
    if aggregated["has_business_income"]:
        print(f"   Business/Professional Income detected")
    if aggregated["has_foreign_assets"]:
        print(f"   Foreign Assets detected")
    
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


@router.get("/download-itr1/{financial_year}")
def download_itr1_report(
    financial_year: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate and download ITR-1 helper PDF report.
    
    This PDF contains all data fields mapped to ITR-1 (SAHAJ) form fields,
    making it easy for the user to fill the official form on the Income Tax portal.
    """
    
    # Get existing tax computation
    computation = db.query(TaxComputation).filter(
        TaxComputation.user_id == current_user.id,
        TaxComputation.financial_year == financial_year
    ).first()

    if generate_helper_report is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ITR helper PDF generation is unavailable. Missing dependency: reportlab."
        )
    
    if not computation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax computation not found. Please calculate tax first."
        )
    
    # Get all verified documents for aggregating data
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.financial_year == financial_year,
        Document.verification_status == VerificationStatus.VERIFIED
    ).all()
    
    # Aggregate document data
    documents_data = aggregate_document_data(documents)
    
    # Prepare user data
    user_data = {
        "name": current_user.name,
        "pan_card": current_user.pan_card,
        "email": current_user.email,
        "date_of_birth": current_user.date_of_birth,
        "gender": current_user.gender.value if current_user.gender else "",
        "mobile": "",  # Not stored in current model
    }
    
    # Convert computation to dict
    computation_dict = {
        "financial_year": computation.financial_year,
        "assessment_year": computation.assessment_year,
        "gross_total_income": computation.gross_total_income,
        "salary_income": computation.salary_income,
        "house_property_income": computation.house_property_income,
        "capital_gains": computation.capital_gains,
        "other_income": computation.other_income,
        
        # Old regime
        "old_regime_deductions": computation.old_regime_deductions or {},
        "old_regime_total_deductions": computation.old_regime_total_deductions,
        "old_regime_taxable_income": computation.old_regime_taxable_income,
        "old_regime_tax_before_rebate": computation.old_regime_tax_before_rebate,
        "old_regime_rebate": computation.old_regime_rebate,
        "old_regime_tax_after_rebate": computation.old_regime_tax_after_rebate,
        "old_regime_surcharge": computation.old_regime_surcharge,
        "old_regime_cess": computation.old_regime_cess,
        "old_regime_total_tax": computation.old_regime_total_tax,
        
        # New regime
        "new_regime_deductions": computation.new_regime_deductions or {},
        "new_regime_total_deductions": computation.new_regime_total_deductions,
        "new_regime_taxable_income": computation.new_regime_taxable_income,
        "new_regime_tax_before_rebate": computation.new_regime_tax_before_rebate,
        "new_regime_rebate": computation.new_regime_rebate,
        "new_regime_tax_after_rebate": computation.new_regime_tax_after_rebate,
        "new_regime_surcharge": computation.new_regime_surcharge,
        "new_regime_cess": computation.new_regime_cess,
        "new_regime_total_tax": computation.new_regime_total_tax,
        
        # Recommendation
        "recommended_regime": computation.recommended_regime,
        "recommendation_reason": computation.recommendation_reason,
        "recommended_itr_form": computation.recommended_itr_form,
        "tax_savings": computation.tax_savings,
        
        # TDS
        "total_tds": computation.total_tds,
        "tax_payable": computation.tax_payable,
        "refund_amount": computation.refund_amount,
    }
    
    try:
        # Get tax rules for this financial year
        try:
            rules_service = RulesService(db, financial_year)
            tax_rules = rules_service.get_all_deduction_limits()
            # Add additional info from rules
            tax_rules['rebate_87a_new'] = rules_service.get_rebate_87a('new_regime')
            tax_rules['rebate_87a_old'] = rules_service.get_rebate_87a('old_regime')
            tax_rules['cess_percent'] = rules_service.get_cess_percent()
            tax_rules['80gg_info'] = rules_service.get_80gg_info()
        except TaxRulesNotFoundError:
            tax_rules = {}  # Will use defaults
        
        # Generate PDF
        pdf_buffer = generate_helper_report(
            user_data=user_data,
            computation=computation_dict,
            documents_data=documents_data,
            financial_year=financial_year,
            tax_rules=tax_rules
        )
        
        # Log activity
        activity = ActivityHistory(
            user_id=current_user.id,
            financial_year=financial_year,
            activity_type="ITR1_REPORT_DOWNLOAD",
            description=f"Downloaded ITR-1 helper report for FY {financial_year}",
            activity_metadata={
                "computation_id": computation.id,
                "recommended_regime": computation.recommended_regime
            }
        )
        db.add(activity)
        db.commit()
        
        # Return PDF as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=ITR1_Helper_{financial_year.replace('-', '_')}.pdf"
            }
        )
        
    except Exception as e:
        print(f"❌ Error generating ITR-1 PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating ITR-1 report: {str(e)}"
        )

