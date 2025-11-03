import json
from core.config import a4f_client, A4F_MODEL

def extract_metadata_from_text(ocr_text: str) -> dict:
    """
    Use A4F GPT-4o-mini to extract structured metadata from OCR text.
    Includes robust JSON parsing and fallback handling.
    """
    if not a4f_client:
        return {
            "detected_type": None,
            "name": None,
            "pan": None,
            "fy": None,
            "ay": None,
            "employer": None,
            "confidence": 0.0,
            "error": "A4F client not initialized or API key missing.",
        }

    prompt = f"""
    You are an expert tax document parser for Indian income tax forms (Form 16, Form 26AS, AIS).

    Extract and return a clean JSON object with the following fields:

    {{
      "Document Type": "Form 16 | Form 26AS | AIS | Unknown",
      "Employee Name": "",
      "Employee PAN": "",
      "Employer Name": "",
      "Employer PAN": "",
      "Assessment Year": "",
      "Financial Year": ""
    }}

    Rules:
    - Always identify both PANs (Employer PAN appears before Employee PAN).
    - If only AY is found, derive FY = (AY_start - 1)-AY_end (e.g., AY 2025-26 → FY 2024-25).
    - Ignore addresses, signatures, or notes.
    - If text contains 'FORM NO. 16' or 'Section 203', set Document Type = "Form 16".
    - Respond ONLY with valid JSON (no text before or after).

    Document text to analyze:
    {ocr_text[:8000]}
    """

    try:
        response = a4f_client.chat.completions.create(
            model=A4F_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional structured data extractor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=800,
        )

        if not response or not response.choices:
            raise ValueError("Empty response from A4F model")

        raw_output = response.choices[0].message.content.strip()

        # ✅ Try to parse JSON safely
        try:
            result = json.loads(raw_output)
        except json.JSONDecodeError:
            print("⚠️ Non-JSON response detected — attempting cleanup")
            json_candidate = raw_output[raw_output.find("{"):raw_output.rfind("}") + 1]
            result = json.loads(json_candidate) if json_candidate else {}

        return {
            "detected_type": result.get("Document Type"),
            "name": result.get("Employee Name"),
            "pan": result.get("Employee PAN"),
            "fy": result.get("Financial Year"),
            "ay": result.get("Assessment Year"),
            "employer": result.get("Employer Name"),
            "employer_pan": result.get("Employer PAN"),
            "confidence": 0.98,
        }

    except Exception as e:
        print(f"⚠️ Extraction failed: {e}")
        return {
            "detected_type": None,
            "name": None,
            "pan": None,
            "fy": None,
            "ay": None,
            "employer": None,
            "confidence": 0.0,
            "error": str(e),
        }
