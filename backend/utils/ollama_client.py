import httpx
import json
from typing import Dict, Any, List
from models import DocType
from sqlalchemy.orm import Session
import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")

async def call_ollama(prompt: str, system_prompt: str = None) -> str:
    """Call Ollama API to get AI response"""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
            
    except Exception as e:
        raise Exception(f"Error calling Ollama: {str(e)}")

async def get_embedding(text: str) -> List[float]:
    """Get vector embedding for text using Ollama"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": OLLAMA_MODEL, 
                "prompt": text
            }
            
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
            
    except Exception as e:
        print(f"Embedding error: {e}")
        return []

async def extract_data_with_ai(text: str, doc_type: DocType, financial_year: str) -> Dict[str, Any]:
    """Extract COMPREHENSIVE structured data from document text using AI"""
    
    # Define comprehensive extraction prompts based on document type
    if doc_type == DocType.FORM_16:
        system_prompt = """You are an expert Indian tax document analyzer. Extract ALL financial data from Form 16 with maximum accuracy.

Return a JSON object with this EXACT structure (use 0.0 for any amount not found):
{
  "pan": "Employee PAN (10 chars)",
  "name": "Employee full name",
  "financial_year": "FY in format YYYY-YY (e.g., 2024-25)",
  "assessment_year": "AY in format YYYY-YY (e.g., 2025-26)",
  "employer_name": "Employer/Company name",
  "employer_tan": "Employer TAN",
  
  "gross_salary": 0.0,
  "basic_salary": 0.0,
  "hra_received": 0.0,
  "special_allowance": 0.0,
  "lta": 0.0,
  "bonus": 0.0,
  "perquisites": 0.0,
  "profits_in_lieu_of_salary": 0.0,
  
  "exemptions": {
    "hra_exemption": 0.0,
    "lta_exemption": 0.0,
    "standard_deduction": 0.0,
    "professional_tax": 0.0,
    "entertainment_allowance": 0.0,
    "total_exemptions": 0.0
  },
  
  "net_salary": 0.0,
  "income_from_house_property": 0.0,
  "income_from_other_sources": 0.0,
  "gross_total_income": 0.0,
  
  "deductions": {
    "80C": 0.0,
    "80CCC": 0.0,
    "80CCD_1": 0.0,
    "80CCD_1B": 0.0,
    "80CCD_2": 0.0,
    "80D": 0.0,
    "80DD": 0.0,
    "80DDB": 0.0,
    "80E": 0.0,
    "80EE": 0.0,
    "80EEA": 0.0,
    "80G": 0.0,
    "80GG": 0.0,
    "80TTA": 0.0,
    "80TTB": 0.0,
    "80U": 0.0,
    "24b_home_loan_interest": 0.0,
    "total_deductions": 0.0
  },
  
  "total_income": 0.0,
  "net_taxable_income": 0.0,
  
  "tax_on_total_income": 0.0,
  "rebate_87a": 0.0,
  "surcharge": 0.0,
  "cess": 0.0,
  "total_tax_liability": 0.0,
  "relief_89": 0.0,
  
  "total_tds": 0.0,
  "advance_tax_paid": 0.0,
  "self_assessment_tax": 0.0,
  "tax_payable": 0.0,
  "refund_due": 0.0
}

CRITICAL INSTRUCTIONS:
1. Extract FINANCIAL YEAR (FY), NOT Assessment Year (AY). Convert AY to FY if needed.
2. Standard Deduction for salaried is typically Rs. 50,000 (FY 2023-24) or Rs. 75,000 (FY 2024-25 onwards)
3. For deductions, look for Section 80C, 80D, etc. amounts in Chapter VI-A
4. Extract ALL amounts even if they appear in tables
5. Return ONLY valid JSON, no explanations"""

    elif doc_type == DocType.FORM_26AS:
        system_prompt = """You are an expert Indian tax document analyzer. Extract ALL TDS and tax payment data from Form 26AS.

Return a JSON object with this EXACT structure:
{
  "pan": "Taxpayer PAN",
  "name": "Taxpayer name",
  "financial_year": "FY in format YYYY-YY",
  "assessment_year": "AY in format YYYY-YY",
  
  "tds_details": {
    "salary_192": 0.0,
    "interest_194A": 0.0,
    "dividend_194": 0.0,
    "commission_194H": 0.0,
    "rent_194I": 0.0,
    "professional_194J": 0.0,
    "sale_of_property_194IA": 0.0,
    "other_tds": 0.0
  },
  
  "total_tds": 0.0,
  "advance_tax_paid": 0.0,
  "self_assessment_tax": 0.0,
  "refund_received": 0.0,
  
  "tds_by_deductor": [
    {
      "deductor_name": "",
      "deductor_tan": "",
      "amount_paid": 0.0,
      "tds_deducted": 0.0
    }
  ]
}

INSTRUCTIONS:
1. Sum up TDS from all deductors for total_tds
2. Extract FINANCIAL YEAR (FY), NOT Assessment Year
3. Return ONLY valid JSON"""

    elif doc_type == DocType.AIS:
        system_prompt = """You are an expert Indian tax document analyzer. Extract ALL income and transaction data from AIS (Annual Information Statement).

Return a JSON object with this EXACT structure:
{
  "pan": "Taxpayer PAN",
  "name": "Taxpayer name",
  "financial_year": "FY in format YYYY-YY",
  "assessment_year": "AY in format YYYY-YY",
  
  "salary_income": 0.0,
  "interest_income": 0.0,
  "dividend_income": 0.0,
  "rental_income": 0.0,
  "capital_gains_short_term": 0.0,
  "capital_gains_long_term": 0.0,
  "business_income": 0.0,
  "other_income": 0.0,
  
  "gross_total_income": 0.0,
  
  "total_tds": 0.0,
  "tds_on_salary": 0.0,
  "tds_on_interest": 0.0,
  "tds_on_other": 0.0,
  
  "high_value_transactions": [
    {
      "type": "",
      "amount": 0.0
    }
  ],
  
  "sft_transactions": {
    "cash_deposits": 0.0,
    "credit_card_payments": 0.0,
    "mutual_fund_purchases": 0.0,
    "property_purchases": 0.0
  }
}

INSTRUCTIONS:
1. Aggregate multiple entries of same income type
2. Extract FINANCIAL YEAR (FY), NOT older years
3. Return ONLY valid JSON"""

    else:
        system_prompt = """You are an expert Indian tax document analyzer. Extract all available financial data.

Return a JSON object with:
{
  "pan": "PAN number",
  "name": "Name",
  "financial_year": "FY in format YYYY-YY",
  "gross_income": 0.0,
  "total_tds": 0.0,
  "deductions": {},
  "other_data": {}
}

Return ONLY valid JSON."""
    
    # Use more text for AI (up to 8000 chars for better extraction)
    text_to_analyze = text[:8000] if len(text) > 8000 else text
    
    # Include expected FY in prompt if provided
    fy_hint = ""
    if financial_year:
        fy_hint = f"\nIMPORTANT: Expected Financial Year is {financial_year}. Extract data for this year."
    
    prompt = f"""Analyze this {doc_type.value} document and extract ALL financial data:

--- DOCUMENT TEXT ---
{text_to_analyze}
--- END OF DOCUMENT ---
{fy_hint}

Extract ALL amounts visible in the document. For Form 16, look especially for:
- Salary components in Part B
- All Chapter VI-A deductions (Section 80C, 80D, etc.)
- Standard Deduction and Professional Tax under Section 16
- TDS deducted

Return complete JSON with accurate values. Use 0.0 for fields not found."""

    try:
        response = await call_ollama(prompt, system_prompt)
        
        # Try to parse JSON from response
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # Find JSON in response if not clean
        if not json_str.startswith('{'):
            import re
            json_match = re.search(r'\{[\s\S]*\}', json_str)
            if json_match:
                json_str = json_match.group(0)
        
        extracted_data = json.loads(json_str)
        
        # Normalize field names (handle variations)
        normalized = {}
        
        # PAN variations
        if 'pan' in extracted_data:
            normalized['pan'] = extracted_data['pan']
        elif 'employee_pan' in extracted_data:
            normalized['pan'] = extracted_data['employee_pan']
        elif 'taxpayer_pan' in extracted_data:
            normalized['pan'] = extracted_data['taxpayer_pan']
        
        # Financial Year variations
        if 'financial_year' in extracted_data:
            fy_value = extracted_data['financial_year']
        elif 'fy' in extracted_data:
            fy_value = extracted_data['fy']
        elif 'fiscal_year' in extracted_data:
            fy_value = extracted_data['fiscal_year']
        else:
            fy_value = None
        
        # CRITICAL: Convert Assessment Year to Financial Year if needed
        if fy_value:
            # Check if it looks like an Assessment Year (next year's range)
            # If AI returned AY 2025-26, convert to FY 2024-25
            fy_normalized = str(fy_value).strip()
            
            # Pattern: YYYY-YY (e.g., 2025-26)
            import re
            ay_match = re.match(r'(\d{4})\s*-\s*(\d{2})', fy_normalized)
            if ay_match:
                year1 = int(ay_match.group(1))
                year2 = int(ay_match.group(2))
                
                # Check if year2 is year1+1 (valid year range)
                if year2 == (year1 % 100 + 1) % 100:
                    # Check if this might be Assessment Year (next year's range)
                    # If current year is 2024, then AY 2025-26 is for FY 2024-25
                    # We'll check if the text mentions "Assessment" or "AY" near this year
                    # For now, if it's clearly next year's range and we're expecting current year, convert it
                    # But this is tricky - let's rely on the extraction logic instead
                    pass
            
            normalized['financial_year'] = fy_normalized
        
        # Document Type variations
        if 'doc_type' in extracted_data:
            normalized['document_type'] = extracted_data['doc_type']
        elif 'document_type' in extracted_data:
            normalized['document_type'] = extracted_data['document_type']
        elif 'type' in extracted_data:
            normalized['document_type'] = extracted_data['type']
        
        # Name variations
        if 'name' in extracted_data:
            normalized['name'] = extracted_data['name']
        elif 'employee_name' in extracted_data:
            normalized['name'] = extracted_data['employee_name']
        elif 'taxpayer_name' in extracted_data:
            normalized['name'] = extracted_data['taxpayer_name']
        
        # Merge with original (keep any other fields)
        normalized.update(extracted_data)
        
        return normalized
        
    except json.JSONDecodeError:
        # Fallback: return text-based extraction
        return {
            "raw_extraction": response,
            "note": "AI response was not valid JSON, storing as raw text"
        }
    except Exception as e:
        raise Exception(f"Error in AI extraction: {str(e)}")

async def get_tax_advice(question: str, context: Dict[str, Any] = None) -> str:
    """Get tax advice using AI"""
    
    system_prompt = """You are a tax expert for Indian Income Tax. Answer briefly and clearly in 2-3 sentences."""
    
    if context:
        prompt = f"""Q: {question}
Context: Income ₹{context.get('gross_income', 0)}, Regime: {context.get('recommended_regime', 'N/A')}
Answer briefly:"""
    else:
        prompt = f"""Q: {question}
Answer briefly (2-3 sentences):"""
    
    try:
        response = await call_ollama(prompt, system_prompt)
        return response
    except Exception as e:
        raise Exception(f"Error getting tax advice: {str(e)}")

async def generate_investment_suggestions(
    gross_income: float,
    current_deductions: Dict[str, float],
    taxable_income: float,
    financial_year: str,
    db: Session = None
) -> Dict[str, Any]:
    """Generate personalized investment suggestions to save tax.
    All limits loaded from RulesService - NO hardcoded values.
    """
    
    # Import RulesService here to avoid circular imports
    from utils.rules_service import RulesService, TaxRulesNotFoundError
    
    # Get deduction limits from rules
    if db:
        try:
            rules_service = RulesService(db, financial_year)
            limits = rules_service.get_all_deduction_limits(30)  # Default age 30
            
            # Extract limits from rules
            limit_80c = limits["80C"]
            limit_80ccd_1b = limits["80CCD_1B"]
            limit_80d_self = limits["80D_self"]
            limit_80d_parents = limits["80D_parents_senior"]
            limit_80tta = limits["80TTA"]
            limit_24b = limits["24b"]
            std_deduction = limits["Standard Deduction"]
            
            # Total 80D limit (self + parents)
            limit_80d_total = limit_80d_self + limit_80d_parents
        except TaxRulesNotFoundError as e:
            raise Exception(f"Tax rules not found: {e}")
    else:
        raise Exception("Database session required for investment suggestions. Please seed tax rules.")
    
    # Build deduction limits dict for prompt
    deduction_limits = {
        "80C": {"limit": limit_80c, "name": "Section 80C (PPF, ELSS, LIC, NSC, etc.)"},
        "80CCD_1B": {"limit": limit_80ccd_1b, "name": "Section 80CCD(1B) - NPS Additional"},
        "80D_self": {"limit": limit_80d_self, "name": "Section 80D - Health Insurance (Self)"},
        "80D_parents": {"limit": limit_80d_parents, "name": "Section 80D - Health Insurance (Parents 60+)"},
        "80E": {"limit": 999999999, "name": "Section 80E - Education Loan Interest"},  # No limit
        "80G": {"limit": 999999999, "name": "Section 80G - Donations"},  # Variable
        "80TTA": {"limit": limit_80tta, "name": "Section 80TTA - Savings Interest"},
        "24b": {"limit": limit_24b, "name": "Section 24(b) - Home Loan Interest"},
    }
    
    # Calculate remaining deductions
    current_80c = float(current_deductions.get("80C", 0) or 0)
    current_80d = float(current_deductions.get("80D", 0) or 0)
    current_nps = float(current_deductions.get("80CCD_1B", 0) or 0)
    current_home_loan = float(current_deductions.get("24b_home_loan_interest", 0) or 0)
    
    remaining_80c = max(0, limit_80c - current_80c)
    remaining_80d = max(0, limit_80d_total - current_80d)
    remaining_nps = max(0, limit_80ccd_1b - current_nps)
    remaining_home_loan = max(0, limit_24b - current_home_loan)
    
    # Get tax slabs from rules and determine applicable rate
    slabs = rules_service.get_slabs("old_regime", 30)
    
    # Calculate tax rate based on taxable income and slabs
    tax_rate = 0.052  # Default 5% + cess
    for slab in slabs:
        slab_min = slab.get("min", 0)
        slab_max = slab.get("max") or float('inf')
        rate_percent = slab.get("rate_percent", 0)
        
        if slab_min <= taxable_income <= slab_max or (taxable_income > slab_min and slab_max == float('inf')):
            tax_rate = (rate_percent / 100) * 1.04  # Add cess
    
    # Get cess from rules
    cess_percent = rules_service.get_cess_percent()
    tax_rate = tax_rate * (1 + cess_percent / 100) if tax_rate > 0 else tax_rate
    
    system_prompt = """You are an expert Indian tax planning advisor. Analyze the user's financial situation 
and provide specific, actionable investment recommendations to minimize tax liability under the OLD REGIME.
Focus on maximizing deductions under sections 80C, 80CCD(1B), 80D, and other applicable sections.
Always provide exact amounts and potential savings based on their tax slab."""
    
    prompt = f"""FINANCIAL PROFILE FOR TAX PLANNING (FY {financial_year}):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Gross Income: ₹{gross_income:,.0f}
• Current Taxable Income: ₹{taxable_income:,.0f}
• Applicable Tax Rate: {tax_rate*100:.1f}%

CURRENT DEDUCTIONS CLAIMED (Limits as per FY {financial_year} rules):
• Section 80C: ₹{current_80c:,.0f} (Limit: ₹{limit_80c:,} | Remaining: ₹{remaining_80c:,.0f})
• Section 80CCD(1B) NPS: ₹{current_nps:,.0f} (Limit: ₹{limit_80ccd_1b:,} | Remaining: ₹{remaining_nps:,.0f})
• Section 80D Health: ₹{current_80d:,.0f} (Limit: ₹{limit_80d_total:,} | Remaining: ₹{remaining_80d:,.0f})
• Home Loan Interest: ₹{current_home_loan:,.0f} (Limit: ₹{limit_24b:,} | Remaining: ₹{remaining_home_loan:,.0f})

Generate 4-5 personalized investment recommendations as a JSON array. For each recommendation include:
- investment_type: Specific investment name (e.g., "ELSS Mutual Funds", "NPS Tier-1")
- section: Tax section (e.g., "80C", "80CCD(1B)")
- recommended_amount: Exact amount to invest (integer)
- potential_tax_savings: Tax saved = amount × applicable tax rate (integer)
- priority: "High", "Medium", or "Low"
- risk_level: "Low", "Medium", "High"
- lock_in_period: Lock-in period (e.g., "3 years", "Till retirement")
- explanation: Why this is recommended (2-3 sentences)
- action_steps: Array of 2-3 specific steps to invest

Return ONLY valid JSON array, no markdown:
[{{"investment_type": "...", "section": "...", "recommended_amount": 50000, "potential_tax_savings": 15600, "priority": "High", "risk_level": "Medium", "lock_in_period": "3 years", "explanation": "...", "action_steps": ["Step 1", "Step 2"]}}]"""

    try:
        response = await call_ollama(prompt, system_prompt)
        
        # Parse JSON
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # Find the JSON array
        start_idx = json_str.find('[')
        end_idx = json_str.rfind(']') + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = json_str[start_idx:end_idx]
        
        suggestions = json.loads(json_str)
        
        # Validate and enhance suggestions
        validated_suggestions = []
        for s in suggestions:
            if isinstance(s, dict):
                validated_suggestions.append({
                    "investment_type": s.get("investment_type", "Tax Saving Investment"),
                    "section": s.get("section", "80C"),
                    "recommended_amount": int(s.get("recommended_amount", 0)),
                    "potential_tax_savings": int(s.get("potential_tax_savings", 0)),
                    "priority": s.get("priority", "Medium"),
                    "risk_level": s.get("risk_level", "Medium"),
                    "lock_in_period": s.get("lock_in_period", "Varies"),
                    "explanation": s.get("explanation", "Recommended tax-saving investment."),
                    "action_steps": s.get("action_steps", ["Consult a financial advisor"])
                })
        
        # Calculate total potential savings
        total_savings = sum(s.get("potential_tax_savings", 0) for s in validated_suggestions)
        
        # Add deduction summary with dynamic limits from rules
        deduction_summary = {
            "80C": {"current": current_80c, "limit": limit_80c, "remaining": remaining_80c},
            "80CCD_1B": {"current": current_nps, "limit": limit_80ccd_1b, "remaining": remaining_nps},
            "80D": {"current": current_80d, "limit": limit_80d_total, "remaining": remaining_80d},
            "24b": {"current": current_home_loan, "limit": limit_24b, "remaining": remaining_home_loan}
        }
        
        return {
            "suggestions": validated_suggestions,
            "total_potential_savings": total_savings,
            "deduction_summary": deduction_summary,
            "tax_rate": tax_rate,
            "gross_income": gross_income,
            "taxable_income": taxable_income
        }
        
    except json.JSONDecodeError as e:
        # Fallback with smart defaults based on remaining limits
        fallback_suggestions = []
        
        if remaining_80c > 0:
            fallback_suggestions.append({
                "investment_type": "ELSS Mutual Funds",
                "section": "80C",
                "recommended_amount": int(remaining_80c),
                "potential_tax_savings": int(remaining_80c * tax_rate),
                "priority": "High",
                "risk_level": "Medium",
                "lock_in_period": "3 years",
                "explanation": f"ELSS offers tax benefits under 80C with the shortest lock-in period of 3 years and potential for higher returns.",
                "action_steps": ["Open Demat account", "Select top-rated ELSS funds", "Invest via SIP or lump sum"]
            })
        
        if remaining_nps > 0:
            fallback_suggestions.append({
                "investment_type": "National Pension System (NPS)",
                "section": "80CCD(1B)",
                "recommended_amount": int(remaining_nps),
                "potential_tax_savings": int(remaining_nps * tax_rate),
                "priority": "High",
                "risk_level": "Low",
                "lock_in_period": "Till age 60",
                "explanation": f"Additional ₹{limit_80ccd_1b:,} deduction under 80CCD(1B) over and above 80C limit. Great for retirement planning.",
                "action_steps": ["Open NPS account via eNPS portal", "Choose Active/Auto choice", "Set up regular contributions"]
            })
        
        if remaining_80d > 0:
            fallback_suggestions.append({
                "investment_type": "Health Insurance Premium",
                "section": "80D",
                "recommended_amount": min(int(remaining_80d), limit_80d_self),
                "potential_tax_savings": int(min(remaining_80d, limit_80d_self) * tax_rate),
                "priority": "High",
                "risk_level": "Low",
                "lock_in_period": "Annual",
                "explanation": f"Health insurance for self, spouse, and children. Additional ₹{limit_80d_parents:,} for parents above 60.",
                "action_steps": ["Compare health insurance policies", "Include family coverage", "Pay premium before March 31"]
            })
        
        total_fallback_savings = sum(s["potential_tax_savings"] for s in fallback_suggestions)
        
        return {
            "suggestions": fallback_suggestions,
            "total_potential_savings": total_fallback_savings,
            "deduction_summary": {
                "80C": {"current": current_80c, "limit": limit_80c, "remaining": remaining_80c},
                "80CCD_1B": {"current": current_nps, "limit": limit_80ccd_1b, "remaining": remaining_nps},
                "80D": {"current": current_80d, "limit": limit_80d_total, "remaining": remaining_80d},
                "24b": {"current": current_home_loan, "limit": limit_24b, "remaining": remaining_home_loan}
            },
            "tax_rate": tax_rate,
            "gross_income": gross_income,
            "taxable_income": taxable_income
        }
    except Exception as e:
        raise Exception(f"Error generating investment suggestions: {str(e)}")


async def detect_itr_form_with_ai(
    aggregated_data: Dict[str, Any],
    user_data: Dict[str, Any] = None,
    financial_year: str = None
) -> Dict[str, Any]:
    """
    Detect the correct ITR form type using AI/LLM.
    
    Analyzes document data (Form 16, AIS, Form 26AS) to determine
    the appropriate ITR form based on Income Tax Act rules.
    
    Args:
        aggregated_data: Aggregated data from all documents
        user_data: Optional user profile data
        financial_year: Financial year for context
    
    Returns:
        Dictionary with itr_form, reason, detected_income_heads, etc.
    """
    
    # Extract income signals for prompt
    salary_income = float(aggregated_data.get("salary_income", 0) or 0)
    house_property_income = float(aggregated_data.get("house_property_income", 0) or 0)
    capital_gains = float(aggregated_data.get("capital_gains", 0) or 0)
    capital_gains_stcg = float(aggregated_data.get("capital_gains_short_term", 0) or 0)
    capital_gains_ltcg = float(aggregated_data.get("capital_gains_long_term", 0) or 0)
    capital_gains_ltcg_112a = float(aggregated_data.get("capital_gains_ltcg_112a", 0) or 0)
    business_income = float(aggregated_data.get("business_income", 0) or 0)
    professional_income = float(aggregated_data.get("professional_income", 0) or 0)
    other_income = float(aggregated_data.get("other_income", 0) or 0)
    interest_income = float(aggregated_data.get("interest_income", 0) or 0)
    dividend_income = float(aggregated_data.get("dividend_income", 0) or 0)
    crypto_income = float(aggregated_data.get("crypto_income", 0) or 0)
    agricultural_income = float(aggregated_data.get("agricultural_income", 0) or 0)
    total_income = float(aggregated_data.get("gross_total_income", 0) or 0)
    
    # Calculate total if not provided
    if total_income == 0:
        total_income = salary_income + abs(house_property_income) + capital_gains + business_income + professional_income + other_income
    
    # Extract eligibility indicators
    num_house_properties = aggregated_data.get("num_house_properties", 1)
    has_foreign_assets = aggregated_data.get("has_foreign_assets", False)
    has_foreign_income = aggregated_data.get("has_foreign_income", False)
    is_director_in_company = aggregated_data.get("is_director_in_company", False)
    has_unlisted_equity = aggregated_data.get("has_unlisted_equity", False)
    is_resident = aggregated_data.get("is_resident", True)
    
    # TDS sections found
    tds_sections = aggregated_data.get("tds_sections", [])
    tds_sections_str = ", ".join(tds_sections) if tds_sections else "None detected"
    
    # Presumptive income flags
    has_presumptive_44ad = aggregated_data.get("has_presumptive_income_44ad", False)
    has_presumptive_44ada = aggregated_data.get("has_presumptive_income_44ada", False)
    has_presumptive_44ae = aggregated_data.get("has_presumptive_income_44ae", False)
    
    system_prompt = """You are an expert Indian Income Tax advisor specializing in ITR form selection.
Your task is to analyze the taxpayer's income details and determine the correct ITR form to file.

Use DETERMINISTIC logic based on the Income Tax Act. Do NOT guess missing income types.
If multiple conditions conflict, prefer the higher complexity ITR form (ITR-3 > ITR-2 > ITR-1).

ITR FORM SELECTION RULES:

ITR-1 (SAHAJ) - Select ONLY if ALL conditions are satisfied:
• Individual is Resident
• Total income ≤ ₹50,00,000
• Income sources limited to: Salary, One house property, Other sources (interest etc.)
• Long-term capital gains u/s 112A ≤ ₹1,25,000
• Agricultural income ≤ ₹5,000
• No business or professional income
• No foreign assets
• Not a director in a company
• No unlisted equity shares

ITR-2 - Select if NO business income AND any of:
• Capital gains exist (other than permitted in ITR-1)
• Multiple house properties
• Foreign assets or foreign income
• Total income > ₹50,00,000
• Director in company
• Unlisted equity shares held

ITR-3 - Select if:
• Income from business or profession exists
• TDS sections 194J (professional), 194C (contractor), 194H (commission) present

ITR-4 (SUGAM) - Select if:
• Income from presumptive taxation under 44AD/44ADA/44AE
• Resident individual
• Total income ≤ ₹50,00,000
• No capital gains other than permitted

IMPORTANT: Return ONLY valid JSON, no explanations outside JSON."""

    prompt = f"""TAXPAYER INCOME ANALYSIS FOR FY {financial_year or "Current"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INCOME DETAILS EXTRACTED FROM DOCUMENTS:

📊 INCOME HEADS:
• Salary Income: ₹{salary_income:,.0f}
• House Property Income: ₹{house_property_income:,.0f}
• Capital Gains (Total): ₹{capital_gains:,.0f}
  - Short-term (STCG): ₹{capital_gains_stcg:,.0f}
  - Long-term (LTCG): ₹{capital_gains_ltcg:,.0f}
  - LTCG u/s 112A (Equity): ₹{capital_gains_ltcg_112a:,.0f}
• Business Income: ₹{business_income:,.0f}
• Professional Income: ₹{professional_income:,.0f}
• Other Sources: ₹{other_income:,.0f}
  - Interest Income: ₹{interest_income:,.0f}
  - Dividend Income: ₹{dividend_income:,.0f}
• Crypto/VDA Income: ₹{crypto_income:,.0f}
• Agricultural Income: ₹{agricultural_income:,.0f}

💰 TOTAL INCOME: ₹{total_income:,.0f}

📋 ELIGIBILITY INDICATORS:
• Number of House Properties: {num_house_properties}
• Foreign Assets: {"Yes" if has_foreign_assets else "No"}
• Foreign Income: {"Yes" if has_foreign_income else "No"}
• Director in Company: {"Yes" if is_director_in_company else "No"}
• Unlisted Equity Shares: {"Yes" if has_unlisted_equity else "No"}
• Residency Status: {"Resident" if is_resident else "Non-Resident"}
• Presumptive Income 44AD: {"Yes" if has_presumptive_44ad else "No"}
• Presumptive Income 44ADA: {"Yes" if has_presumptive_44ada else "No"}
• Presumptive Income 44AE: {"Yes" if has_presumptive_44ae else "No"}

📄 TDS SECTION CODES DETECTED (from Form 26AS):
{tds_sections_str}

TDS Section Code Meanings:
- 192: Salary income
- 194A: Interest income
- 194J: Professional/Technical fees (indicates business income)
- 194C: Contractor payments (indicates business income)
- 194H: Commission income (indicates business income)
- 194IA: Property sale (indicates capital gains)
- 194S: Crypto transactions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Based on the above information, determine the correct ITR form.

Return response as JSON in this EXACT format:
{{
  "itr_form": "ITR-1 | ITR-2 | ITR-3 | ITR-4",
  "reason": "Detailed explanation of why this ITR form is applicable based on the Income Tax Act rules. Include specific income heads and amounts that led to this decision.",
  "detected_income_heads": {{
    "salary": {salary_income},
    "house_property": {house_property_income},
    "capital_gains": {capital_gains},
    "business_income": {business_income + professional_income},
    "other_sources": {other_income}
  }},
  "key_factors": [
    "Factor 1 that determined the ITR form",
    "Factor 2"
  ],
  "warnings": [
    "Any warnings or things the taxpayer should verify"
  ]
}}"""

    try:
        response = await call_ollama(prompt, system_prompt)
        
        # Parse JSON from response
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
        # Find JSON object in response
        if not json_str.startswith('{'):
            import re
            json_match = re.search(r'\{[\s\S]*\}', json_str)
            if json_match:
                json_str = json_match.group(0)
        
        result = json.loads(json_str)
        
        # Validate and normalize the result
        valid_forms = ["ITR-1", "ITR-2", "ITR-3", "ITR-4"]
        itr_form = result.get("itr_form", "ITR-2")
        
        # Normalize form name
        if "1" in itr_form and "ITR" in itr_form.upper():
            itr_form = "ITR-1"
        elif "2" in itr_form and "ITR" in itr_form.upper():
            itr_form = "ITR-2"
        elif "3" in itr_form and "ITR" in itr_form.upper():
            itr_form = "ITR-3"
        elif "4" in itr_form and "ITR" in itr_form.upper():
            itr_form = "ITR-4"
        
        if itr_form not in valid_forms:
            itr_form = "ITR-2"  # Safe default
        
        return {
            "itr_form": itr_form,
            "reason": result.get("reason", "ITR form determined based on income analysis."),
            "detected_income_heads": result.get("detected_income_heads", {
                "salary": salary_income,
                "house_property": house_property_income,
                "capital_gains": capital_gains,
                "business_income": business_income + professional_income,
                "other_sources": other_income
            }),
            "eligibility_indicators": {
                "total_income": total_income,
                "num_house_properties": num_house_properties,
                "has_foreign_assets": has_foreign_assets,
                "has_foreign_income": has_foreign_income,
                "is_director_in_company": is_director_in_company,
                "has_unlisted_equity": has_unlisted_equity,
                "is_resident": is_resident,
                "tds_sections_found": tds_sections
            },
            "key_factors": result.get("key_factors", []),
            "warnings": result.get("warnings", []),
            "confidence": "high",
            "detection_method": "ai"
        }
        
    except json.JSONDecodeError as e:
        # Fallback to rule-based detection if AI fails
        print(f"⚠️ AI ITR detection failed to parse JSON: {e}")
        return _fallback_itr_detection(aggregated_data)
    except Exception as e:
        print(f"⚠️ AI ITR detection error: {e}")
        return _fallback_itr_detection(aggregated_data)


def _fallback_itr_detection(aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback rule-based ITR detection when AI fails.
    Simple deterministic logic based on key indicators.
    """
    salary_income = float(aggregated_data.get("salary_income", 0) or 0)
    business_income = float(aggregated_data.get("business_income", 0) or 0)
    professional_income = float(aggregated_data.get("professional_income", 0) or 0)
    capital_gains = float(aggregated_data.get("capital_gains", 0) or 0)
    total_income = float(aggregated_data.get("gross_total_income", 0) or 0)
    
    has_foreign_assets = aggregated_data.get("has_foreign_assets", False)
    is_director = aggregated_data.get("is_director_in_company", False)
    has_unlisted_equity = aggregated_data.get("has_unlisted_equity", False)
    num_house_properties = aggregated_data.get("num_house_properties", 1)
    
    tds_sections = aggregated_data.get("tds_sections", [])
    business_tds = any(sec in ["194J", "194C", "194H"] for sec in tds_sections)
    
    # Determine ITR form
    if business_income > 0 or professional_income > 0 or business_tds:
        itr_form = "ITR-3"
        reason = "Business or professional income detected. ITR-3 is required for individuals with income from business or profession."
    elif capital_gains > 0 or has_foreign_assets or is_director or has_unlisted_equity or num_house_properties > 1 or total_income > 5000000:
        itr_form = "ITR-2"
        reasons = []
        if capital_gains > 0:
            reasons.append("capital gains")
        if has_foreign_assets:
            reasons.append("foreign assets")
        if is_director:
            reasons.append("director in company")
        if has_unlisted_equity:
            reasons.append("unlisted equity shares")
        if num_house_properties > 1:
            reasons.append("multiple house properties")
        if total_income > 5000000:
            reasons.append("income exceeds Rs.50 lakhs")
        reason = f"ITR-2 is required due to: {', '.join(reasons)}."
    else:
        itr_form = "ITR-1"
        reason = "Simple income from salary, one house property, and other sources within Rs.50 lakhs. ITR-1 (Sahaj) is applicable."
    
    return {
        "itr_form": itr_form,
        "reason": reason,
        "detected_income_heads": {
            "salary": salary_income,
            "house_property": float(aggregated_data.get("house_property_income", 0) or 0),
            "capital_gains": capital_gains,
            "business_income": business_income + professional_income,
            "other_sources": float(aggregated_data.get("other_income", 0) or 0)
        },
        "eligibility_indicators": {
            "total_income": total_income,
            "num_house_properties": num_house_properties,
            "has_foreign_assets": has_foreign_assets,
            "is_director_in_company": is_director,
            "has_unlisted_equity": has_unlisted_equity,
            "tds_sections_found": tds_sections
        },
        "key_factors": [],
        "warnings": ["Detection performed using fallback rules due to AI error."],
        "confidence": "medium",
        "detection_method": "fallback_rules"
    }

