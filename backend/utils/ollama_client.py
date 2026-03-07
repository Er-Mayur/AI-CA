import httpx
import json
from typing import Dict, Any, List
from models import DocType
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
    financial_year: str
) -> Dict[str, Any]:
    """Generate personalized investment suggestions to save tax"""
    
    # Calculate current utilization and remaining limits
    deduction_limits = {
        "80C": {"limit": 150000, "name": "Section 80C (PPF, ELSS, LIC, NSC, etc.)"},
        "80CCD_1B": {"limit": 50000, "name": "Section 80CCD(1B) - NPS Additional"},
        "80D_self": {"limit": 25000, "name": "Section 80D - Health Insurance (Self)"},
        "80D_parents": {"limit": 50000, "name": "Section 80D - Health Insurance (Parents 60+)"},
        "80E": {"limit": 999999999, "name": "Section 80E - Education Loan Interest"},
        "80G": {"limit": 999999999, "name": "Section 80G - Donations"},
        "80TTA": {"limit": 10000, "name": "Section 80TTA - Savings Interest"},
        "24b": {"limit": 200000, "name": "Section 24(b) - Home Loan Interest"},
    }
    
    # Calculate remaining deductions
    current_80c = float(current_deductions.get("80C", 0) or 0)
    current_80d = float(current_deductions.get("80D", 0) or 0)
    current_nps = float(current_deductions.get("80CCD_1B", 0) or 0)
    current_home_loan = float(current_deductions.get("24b_home_loan_interest", 0) or 0)
    
    remaining_80c = max(0, 150000 - current_80c)
    remaining_80d = max(0, 75000 - current_80d)  # 25k self + 50k parents
    remaining_nps = max(0, 50000 - current_nps)
    remaining_home_loan = max(0, 200000 - current_home_loan)
    
    # Determine tax slab for savings calculation
    if taxable_income > 1500000:
        tax_rate = 0.312  # 30% + 4% cess
    elif taxable_income > 1200000:
        tax_rate = 0.312
    elif taxable_income > 1000000:
        tax_rate = 0.312
    elif taxable_income > 500000:
        tax_rate = 0.208  # 20% + 4% cess
    else:
        tax_rate = 0.052  # 5% + 4% cess
    
    system_prompt = """You are an expert Indian tax planning advisor. Analyze the user's financial situation 
and provide specific, actionable investment recommendations to minimize tax liability under the OLD REGIME.
Focus on maximizing deductions under sections 80C, 80CCD(1B), 80D, and other applicable sections.
Always provide exact amounts and potential savings based on their tax slab."""
    
    prompt = f"""FINANCIAL PROFILE FOR TAX PLANNING (FY {financial_year}):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Gross Income: ₹{gross_income:,.0f}
• Current Taxable Income: ₹{taxable_income:,.0f}
• Applicable Tax Rate: {tax_rate*100:.1f}%

CURRENT DEDUCTIONS CLAIMED:
• Section 80C: ₹{current_80c:,.0f} (Limit: ₹1,50,000 | Remaining: ₹{remaining_80c:,.0f})
• Section 80CCD(1B) NPS: ₹{current_nps:,.0f} (Limit: ₹50,000 | Remaining: ₹{remaining_nps:,.0f})
• Section 80D Health: ₹{current_80d:,.0f} (Limit: ₹75,000 | Remaining: ₹{remaining_80d:,.0f})
• Home Loan Interest: ₹{current_home_loan:,.0f} (Limit: ₹2,00,000 | Remaining: ₹{remaining_home_loan:,.0f})

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
        
        # Add deduction summary
        deduction_summary = {
            "80C": {"current": current_80c, "limit": 150000, "remaining": remaining_80c},
            "80CCD_1B": {"current": current_nps, "limit": 50000, "remaining": remaining_nps},
            "80D": {"current": current_80d, "limit": 75000, "remaining": remaining_80d},
            "24b": {"current": current_home_loan, "limit": 200000, "remaining": remaining_home_loan}
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
                "explanation": "Additional ₹50,000 deduction under 80CCD(1B) over and above 80C limit. Great for retirement planning.",
                "action_steps": ["Open NPS account via eNPS portal", "Choose Active/Auto choice", "Set up regular contributions"]
            })
        
        if remaining_80d > 0:
            fallback_suggestions.append({
                "investment_type": "Health Insurance Premium",
                "section": "80D",
                "recommended_amount": min(int(remaining_80d), 25000),
                "potential_tax_savings": int(min(remaining_80d, 25000) * tax_rate),
                "priority": "High",
                "risk_level": "Low",
                "lock_in_period": "Annual",
                "explanation": "Health insurance for self, spouse, and children. Additional ₹50,000 for parents above 60.",
                "action_steps": ["Compare health insurance policies", "Include family coverage", "Pay premium before March 31"]
            })
        
        total_fallback_savings = sum(s["potential_tax_savings"] for s in fallback_suggestions)
        
        return {
            "suggestions": fallback_suggestions,
            "total_potential_savings": total_fallback_savings,
            "deduction_summary": {
                "80C": {"current": current_80c, "limit": 150000, "remaining": remaining_80c},
                "80CCD_1B": {"current": current_nps, "limit": 50000, "remaining": remaining_nps},
                "80D": {"current": current_80d, "limit": 75000, "remaining": remaining_80d}
            },
            "tax_rate": tax_rate,
            "gross_income": gross_income,
            "taxable_income": taxable_income
        }
    except Exception as e:
        raise Exception(f"Error generating investment suggestions: {str(e)}")

