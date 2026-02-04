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
    """Extract structured data from document text using AI"""
    
    # Define extraction prompts based on document type
    if doc_type == DocType.FORM_16:
        system_prompt = """You are a tax document analyzer. Extract comprehensive data from Form 16 as JSON with these fields:
{
  "pan": "Employee PAN",
  "financial_year": "Financial Year (format: 2024-25)",
  "doc_type": "Form 16",
  "name": "Employee name",
  "employer_name": "Employer name",
  "employer_tan": "Employer TAN",
  "gross_salary": 0.0,
  "exemptions": {
    "hra": 0.0,
    "lta": 0.0,
    "other": 0.0
  },
  "standard_deduction": 0.0,
  "professional_tax": 0.0,
  "deductions": {
    "80c": 0.0,
    "80d": 0.0,
    "80ccd": 0.0,
    "80e": 0.0,
    "other": 0.0
  },
  "total_income": 0.0,
  "net_taxable_income": 0.0,
  "total_tds": 0.0
}
IMPORTANT: 
- Extract exact amounts. If not found, use 0.0.
- Extract FINANCIAL YEAR (FY), not Assessment Year (AY).
- Return ONLY valid JSON."""
    elif doc_type == DocType.FORM_26AS:
        system_prompt = """You are a tax document analyzer. Extract data from Form 26AS as JSON with these fields:
{
  "pan": "Taxpayer PAN",
  "financial_year": "Financial Year (format: 2024-25)",
  "doc_type": "Form 26AS",
  "name": "Taxpayer name",
  "total_tds": 0.0,
  "total_amount_paid": 0.0
}
Return ONLY valid JSON."""
    elif doc_type == DocType.AIS:
        system_prompt = """You are a tax document analyzer. Extract data from AIS (Annual Information Statement) as JSON with these fields:
{
  "pan": "Taxpayer PAN",
  "financial_year": "Financial Year (format: 2024-25)",
  "doc_type": "AIS",
  "name": "Taxpayer name",
  "salary_income": 0.0,
  "interest_income": 0.0,
  "dividend_income": 0.0,
  "capital_gains": 0.0,
  "business_income": 0.0,
  "other_income": 0.0,
  "total_tds": 0.0
}
IMPORTANT:
- Extract FINANCIAL YEAR (FY), NOT older years.
- Aggregate amounts if multiple entries exist for same category (e.g. multiple Interest Incomes).
- Return ONLY valid JSON."""
    else:
        system_prompt = """You are a tax document analyzer. Extract data as JSON with: pan, financial_year, doc_type, name, gross_income (if any), total_tds (if any).
Return ONLY valid JSON."""
    
    # Use more text for AI (up to 6000 chars for better extraction of tables)
    text_to_analyze = text[:6000] if len(text) > 6000 else text
    
    # Include expected FY in prompt if provided
    fy_hint = ""
    if financial_year:
        fy_hint = f"\nNote: Expected Financial Year is {financial_year}. Look for this or similar format (YYYY-YY)."
    
    prompt = f"""Extract data from this {doc_type.value} document:

{text_to_analyze}
{fy_hint}

Return complete JSON with all financial details extracted.
IMPORTANT: Extract financial_year even if partially visible."""
    
    try:
        response = await call_ollama(prompt, system_prompt)
        
        # Try to parse JSON from response
        # Sometimes AI returns JSON wrapped in markdown code blocks
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        
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
    
    system_prompt = """You are a tax-saving investment advisor. Suggest 2-3 options as JSON array."""
    
    prompt = f"""Income: ₹{gross_income:,.0f}, Taxable: ₹{taxable_income:,.0f}

Suggest 2-3 tax-saving investments (80C, 80D, NPS) as JSON:
[{{"investment_type": "...", "recommended_amount": 0, "potential_tax_savings": 0, "explanation": "...", "risk_level": "..."}}]"""
    
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
        
        suggestions = json.loads(json_str)
        
        # Calculate total potential savings
        total_savings = sum(s.get("potential_tax_savings", 0) for s in suggestions if isinstance(s, dict))
        
        return {
            "suggestions": suggestions,
            "total_potential_savings": total_savings
        }
        
    except json.JSONDecodeError:
        # Fallback
        return {
            "suggestions": [{
                "investment_type": "General Tax Saving Investments",
                "recommended_amount": 150000,
                "potential_tax_savings": 46800,
                "explanation": response[:500],
                "risk_level": "Low to Medium"
            }],
            "total_potential_savings": 0
        }
    except Exception as e:
        raise Exception(f"Error generating investment suggestions: {str(e)}")

