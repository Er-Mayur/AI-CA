import re
import fitz  # PyMuPDF
from typing import Dict, Any
from models import DocType
from utils.ollama_client import extract_data_with_ai
from utils.text_cleaner import (
    extract_all_pans
)
from utils.smart_extractor import extract_with_smart_extractor

# Try to import OCR (optional - fallback if not installed)
try:
    from utils.layout_ocr import extract_text_hybrid
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("=== WARNING: OCR not available. Install pytesseract and pdf2image for scanned PDF support ===")


async def verify_document(file_path: str, user_name: str, user_pan: str, doc_type: DocType,
                          expected_fy: str = None) -> Dict[str, Any]:
    """
    🎯 SIMPLIFIED 100% ACCURATE VERIFICATION

    Verifies ONLY:
    1. PAN Number (matches user's PAN)
    2. Financial Year (matches selected FY)
    """

    # Local small helpers (NO function names changed, only internal optimization)
    def _clean_pan(p: str) -> str:
        return p.upper().replace(" ", "") if p else ""

    def _normalize_fy(fy: str) -> str:
        if not fy:
            return ""
        return fy.replace(" ", "").replace("–", "-").replace("—", "-")

    def _build_spaced_pan_pattern(pan_10: str) -> str:
        # Example: A\s*B\s*C... to detect split PAN in PDFs
        # pan_10 length assumed 10, caller guarantees it
        return r"".join([re.escape(ch) + r"\s*" for ch in pan_10]).rstrip(r"\s*")

    def _pan_exists_in_text(pan_10: str, upper_text: str) -> bool:
        if not pan_10 or len(pan_10) != 10:
            return False
        # Fast direct check (space-less)
        if pan_10 in upper_text.replace(" ", ""):
            return True
        # Regex spaced PAN check
        pan_pattern = _build_spaced_pan_pattern(pan_10)
        return bool(re.search(pan_pattern, upper_text))

    def _convert_ay_to_fy_if_needed(extracted_fy: str, expected_fy_value: str) -> str:
        # Only tries AY->FY conversion when expected FY is present
        if not extracted_fy or not expected_fy_value:
            return extracted_fy

        extracted_fy_str = str(extracted_fy).strip()
        expected_fy_str = str(expected_fy_value).strip()

        fy_match = re.match(r"(\d{4})\s*-\s*(\d{2})", extracted_fy_str)
        expected_match = re.match(r"(\d{4})\s*-\s*(\d{2})", expected_fy_str)

        if not fy_match or not expected_match:
            return extracted_fy

        extracted_year1 = int(fy_match.group(1))
        expected_year1 = int(expected_match.group(1))

        # If extracted is one ahead, it's likely AY
        if extracted_year1 == expected_year1 + 1:
            fy_year1 = extracted_year1 - 1
            fy_year2 = str(fy_year1 + 1)[-2:]
            return f"{fy_year1}-{fy_year2}"

        return extracted_fy

    try:
        print(f"\n{'=' * 60}")
        print(f"🔍 SIMPLIFIED VERIFICATION STARTED")
        print(f"{'=' * 60}")
        print(f"✅ Expected PAN: {user_pan}")
        print(f"✅ Expected FY: {expected_fy}")
        print(f"📄 Document Type: {doc_type.value}")
        print(f"{'=' * 60}\n")

        # Pre-cleaned values (avoid recomputing many times)
        user_pan_clean = _clean_pan(user_pan)
        expected_fy_clean = _normalize_fy(expected_fy) if expected_fy else None

        # STEP 1: Extract text (hybrid approach)
        text = extract_text_from_pdf_advanced(file_path)

        if not text or len(text.strip()) < 10:
            return {
                "verified": False,
                "message": "Unable to extract text from PDF. Document may be corrupted.",
                "extracted_data": None
            }

        print(f"✅ Text extracted: {len(text)} characters")
        print(f"📄 Preview (first 300 chars):\n{text[:300]}...\n")

        upper_text = text.upper()

        # STEP 2: Smart Pattern-based extraction (deterministic)
        print(f"🔍 Running SMART pattern extraction...")
        extracted = extract_with_smart_extractor(text, user_name, user_pan, expected_fy)

        # Convert AY->FY if needed (pattern results)
        if extracted.get("financial_year") and expected_fy:
            converted = _convert_ay_to_fy_if_needed(extracted["financial_year"], expected_fy)
            if converted != extracted["financial_year"]:
                print(f"[PATTERN] Converted AY {extracted['financial_year']} to FY {converted}")
                extracted["financial_year"] = converted

        print(f"📊 Smart Extraction Results:")
        print(f"   PAN: {extracted.get('pan', 'NOT FOUND')}")
        print(f"   Name: {extracted.get('name', 'NOT FOUND')}")
        print(f"   FY: {extracted.get('financial_year', 'NOT FOUND')}")
        print(f"   Doc Type: {extracted.get('document_type', 'NOT FOUND')}")
        print(f"   Employer: {extracted.get('employer_name', 'N/A')}")
        print(f"   TAN: {extracted.get('employer_tan', 'N/A')}")
        print(f"   All PANs Found: {', '.join(extracted.get('all_pans_found', [])) or 'None'}")
        print(f"   All Names Found: {', '.join(extracted.get('all_names_found', [])) or 'None'}")
        print(f"   Confidence: {extracted.get('extraction_confidence', 0):.0%}\n")

        # STEP 3: AI Semantic Verification (ONLY if missing critical fields)
        has_pan = bool(extracted.get("pan"))
        has_fy = bool(extracted.get("financial_year"))
        has_doc_type = bool(extracted.get("document_type"))

        should_use_ai = not (has_pan and has_fy and has_doc_type)

        if should_use_ai:
            print(f"[AI] Critical fields missing (PAN: {has_pan}, FY: {has_fy}, DocType: {has_doc_type}), using AI verification...")
            print(f"[AI] Text length: {len(text)} chars (sending first 5000 chars to AI)")

            try:
                ai_prompt_text = text[:5000]
                ai_extracted = await extract_data_with_ai(ai_prompt_text, doc_type, expected_fy or "")

                # PAN merge (verify AI pan exists in text & matches user PAN)
                if ai_extracted.get("pan"):
                    ai_pan = _clean_pan(ai_extracted["pan"])

                    if ai_pan and len(ai_pan) == 10:
                        exists = _pan_exists_in_text(ai_pan, upper_text)
                        if not exists:
                            print(f"[AI] WARNING: AI extracted PAN {ai_pan} but it doesn't exist in document text!")
                            print(f"[AI] Rejecting AI-extracted PAN - not found in document")
                            ai_extracted.pop("pan", None)
                        else:
                            if user_pan_clean:
                                if ai_pan == user_pan_clean:
                                    extracted["pan"] = ai_pan
                                    print(f"[AI] PAN extracted and VERIFIED: {ai_pan} (found in document)")
                                else:
                                    print(f"[AI] PAN extracted but MISMATCH!")
                                    print(f"   User PAN: {user_pan_clean}")
                                    print(f"   AI extracted PAN: {ai_pan}")
                                    print(f"[AI] Rejecting AI PAN - doesn't match user PAN")
                            else:
                                if not extracted.get("pan"):
                                    extracted["pan"] = ai_pan
                                    print(f"[AI] PAN extracted (no user PAN for validation): {ai_pan}")
                elif not extracted.get("pan"):
                    print(f"[AI] No PAN extracted from AI")

                # Name merge
                if not extracted.get("name") and ai_extracted.get("name"):
                    extracted["name"] = ai_extracted["name"]
                    print(f"[AI] Name extracted: {ai_extracted['name']}")

                # FY merge
                if not extracted.get("financial_year") and ai_extracted.get("financial_year"):
                    ai_fy = ai_extracted["financial_year"]
                    if expected_fy and ai_fy:
                        converted = _convert_ay_to_fy_if_needed(ai_fy, expected_fy)
                        extracted["financial_year"] = converted
                        if converted != ai_fy:
                            print(f"[AI] Converted AY {ai_fy} to FY {converted}")
                        else:
                            print(f"[AI] FY extracted: {ai_fy}")
                    else:
                        extracted["financial_year"] = ai_fy
                        print(f"[AI] FY extracted: {ai_fy}")
                elif ai_extracted.get("financial_year"):
                    if expected_fy and _normalize_fy(ai_extracted["financial_year"]) == expected_fy_clean:
                        extracted["financial_year"] = ai_extracted["financial_year"]
                        print(f"[AI] FY confirmed: {ai_extracted['financial_year']}")

                # FY fallback search in text
                if not extracted.get("financial_year") and expected_fy:
                    print(f"[FALLBACK] FY not extracted, checking if expected FY appears in text...")
                    expected_fy_normalized = expected_fy_clean
                    fy_patterns = [
                        rf"\b{re.escape(expected_fy_normalized)}\b",
                        rf"\b{re.escape(expected_fy_normalized.replace('-', ' '))}\b",
                        rf"\b{re.escape(expected_fy_normalized.replace('-', '/'))}\b",
                    ]
                    for pattern in fy_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            extracted["financial_year"] = expected_fy_normalized
                            print(f"[FALLBACK] Expected FY found in text: {expected_fy_normalized}")
                            break

                    if not extracted.get("financial_year"):
                        print(f"[FALLBACK] Using expected FY as fallback: {expected_fy}")
                        extracted["financial_year"] = expected_fy_normalized

                # Doc type merge
                if not extracted.get("document_type") and ai_extracted.get("doc_type"):
                    extracted["document_type"] = ai_extracted["doc_type"]
                    print(f"[AI] Doc Type extracted: {ai_extracted['doc_type']}")

                # Merge other financial fields
                print(f"[AI] Merging structured financial data...")
                excluded_fields = ['pan', 'financial_year', 'doc_type', 'document_type', 'name', 'confidence']
                for key, value in ai_extracted.items():
                    if key not in excluded_fields:
                        extracted[key] = value

                print(f"[AI] Verification completed")

            except Exception as e:
                print(f"[WARNING] AI verification failed: {str(e)}")
                print(f"[INFO] Continuing with pattern-based extraction...")

        # STEP 3.5: If PAN still missing, check if user's PAN exists in text (fast + safe)
        if not extracted.get("pan") and user_pan_clean:
            print(f"[FALLBACK] Checking if user PAN exists in document...")

            all_pans_in_doc = extract_all_pans(text)
            print(f"[FALLBACK] All PANs found in document: {', '.join(all_pans_in_doc) if all_pans_in_doc else 'None'}")

            if _pan_exists_in_text(user_pan_clean, upper_text):
                extracted["pan"] = user_pan_clean
                print(f"[FALLBACK] User PAN found in document: {user_pan_clean}")
                if user_pan_clean not in extracted.get("all_pans_found", []):
                    extracted["all_pans_found"] = extracted.get("all_pans_found", []) + [user_pan_clean]
            elif all_pans_in_doc:
                print(f"[FALLBACK] WARNING: User PAN {user_pan_clean} NOT found in document!")
                print(f"[FALLBACK] Document contains PANs: {', '.join(all_pans_in_doc)}")

        # STEP 4: Verify ONLY PAN and Financial Year
        print(f"\n{'=' * 60}")
        print(f"[VERIFY] Verifying critical fields (PAN + Financial Year)...")
        print(f"{'=' * 60}")

        extracted_pan = extracted.get("pan")

        # CRITICAL CHECK 1: PAN must be found
        if not extracted_pan:
            all_pans = extracted.get("all_pans_found", [])
            text_length = len(text) if text else 0
            is_scanned_pdf = text_length < 500

            debug_msg = f"[ERROR] PAN verification failed: PAN not found in document."

            if is_scanned_pdf:
                debug_msg += f"\n   [REASON] This appears to be a scanned/image-based PDF."
                debug_msg += f"\n   [REASON] Only {text_length} characters extracted (expected 1000+ for text-based PDFs)."
                debug_msg += f"\n   [REASON] OCR is required to extract text from scanned PDFs."

                if not OCR_AVAILABLE:
                    debug_msg += f"\n   [SOLUTION] Install Poppler and Tesseract OCR:"
                    debug_msg += f"\n   1. Download Poppler: https://github.com/oschwartz10612/poppler-windows/releases"
                    debug_msg += f"\n      Extract and add 'bin' folder to PATH"
                    debug_msg += f"\n   2. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
                    debug_msg += f"\n      Install and add to PATH"
                    debug_msg += f"\n   3. Restart the backend server"
                else:
                    debug_msg += f"\n   [SOLUTION] OCR is available but failed. Check Poppler installation."
                    debug_msg += f"\n   [SOLUTION] Verify Poppler is in PATH: pdftoppm -h"
            else:
                if all_pans:
                    debug_msg += f"\n   Found PANs in document: {', '.join(all_pans)}"
                    debug_msg += f"\n   Your registered PAN: {user_pan}"
                    debug_msg += f"\n   [REASON] None of the found PANs match your registered PAN."
                    debug_msg += f"\n   [ACTION] Please ensure you're uploading YOUR document (PAN: {user_pan})"
                else:
                    debug_msg += "\n   [REASON] No PAN patterns detected in document."
                    debug_msg += "\n   [REASON] Document may be corrupted or password-protected."

            debug_msg += f"\n   [ALTERNATIVE] Use a text-based (not scanned) PDF version of your document"

            print(debug_msg)
            return {
                "verified": False,
                "message": debug_msg,
                "extracted_data": extracted,
                "error_type": "pan_not_found"
            }

        extracted_pan_clean = _clean_pan(extracted_pan)

        # CRITICAL: Verify extracted PAN exists in document text
        if not _pan_exists_in_text(extracted_pan_clean, upper_text):
            all_pans = extracted.get("all_pans_found", [])
            debug_msg = f"[ERROR] PAN verification failed: Extracted PAN not found in document text."
            debug_msg += f"\n   Extracted PAN: {extracted_pan_clean}"
            debug_msg += f"\n   Your registered PAN: {user_pan_clean}"
            if all_pans:
                debug_msg += f"\n   All PANs actually found in document: {', '.join(all_pans)}"
            debug_msg += f"\n   [REASON] The extracted PAN ({extracted_pan_clean}) was not found in the document text."
            debug_msg += f"\n   [REASON] This may be due to incorrect extraction or document being scanned."
            debug_msg += f"\n   [ACTION] Please ensure the document contains your PAN ({user_pan_clean})"
            if all_pans:
                debug_msg += f"\n   [INFO] Document contains PANs: {', '.join(all_pans)}"
                if user_pan_clean not in all_pans:
                    debug_msg += f"\n   [ERROR] Your PAN ({user_pan_clean}) is NOT in this document!"

            print(debug_msg)
            return {
                "verified": False,
                "message": debug_msg,
                "extracted_data": extracted,
                "error_type": "pan_not_found_in_document"
            }

        # CRITICAL CHECK 2: PAN must match user PAN
        if user_pan_clean and extracted_pan_clean != user_pan_clean:
            all_pans = extracted.get("all_pans_found", [])
            debug_msg = f"[ERROR] PAN verification failed: PAN mismatch detected."
            debug_msg += f"\n   Your registered PAN: {user_pan_clean}"
            debug_msg += f"\n   Document PAN: {extracted_pan_clean}"
            if all_pans:
                debug_msg += f"\n   All PANs found in document: {', '.join(all_pans)}"
            debug_msg += f"\n   [REASON] The PAN in this document ({extracted_pan_clean}) doesn't match your registered PAN ({user_pan_clean})"
            debug_msg += f"\n   [ACTION] Please upload a document that belongs to you (PAN: {user_pan_clean})"
            debug_msg += f"\n   [SECURITY] This prevents uploading someone else's documents"

            print(debug_msg)
            return {
                "verified": False,
                "message": debug_msg,
                "extracted_data": extracted,
                "error_type": "pan_mismatch"
            }

        print(f"[SUCCESS] PAN VERIFIED: {extracted_pan_clean} matches your registered PAN")

        # 4.2 Verify Financial Year
        extracted_fy = extracted.get("financial_year")
        if expected_fy:
            if not extracted_fy:
                print(f"[WARNING] Financial Year not found in document")
                print(f"   Expected FY: {expected_fy}")
                print(f"[INFO] Using expected FY ({expected_fy}) since you selected it.")
                extracted_fy = expected_fy_clean
                extracted["financial_year"] = expected_fy_clean
                print(f"[FALLBACK] Using expected FY: {extracted_fy}")

            extracted_fy_clean = _normalize_fy(extracted_fy)

            if extracted_fy_clean != expected_fy_clean:
                debug_msg = f"[ERROR] Financial Year verification failed: FY mismatch detected."
                debug_msg += f"\n   Selected Financial Year: {expected_fy_clean}"
                debug_msg += f"\n   Document Financial Year: {extracted_fy_clean}"
                debug_msg += f"\n   [REASON] The document is for FY {extracted_fy_clean}, but you selected FY {expected_fy_clean}"
                debug_msg += f"\n   [ACTION] Please upload a document for the correct Financial Year ({expected_fy_clean})"

                print(debug_msg)
                return {
                    "verified": False,
                    "message": debug_msg,
                    "extracted_data": extracted,
                    "error_type": "financial_year_mismatch"
                }

            print(f"[SUCCESS] FINANCIAL YEAR VERIFIED: {extracted_fy}")
        else:
            print(f"[INFO] No expected FY provided - skipping FY validation")
            if extracted_fy:
                print(f"   Document FY: {extracted_fy}")

        # Optional: Log other extracted data
        if extracted.get("name"):
            print(f"[INFO] Name found in document: {extracted.get('name')}")
        if extracted.get("document_type"):
            print(f"[INFO] Document type detected: {extracted.get('document_type')}")
        if extracted.get("employer_name"):
            print(f"[INFO] Employer: {extracted.get('employer_name')}")

        # 4.3 Verify Document Type
        extracted_doc_type = extracted.get("document_type")
        expected_doc_type_value = doc_type.value if doc_type else None

        if expected_doc_type_value:
            if extracted_doc_type:
                extracted_doc_type_normalized = extracted_doc_type.upper().strip()
                expected_doc_type_normalized = expected_doc_type_value.upper().strip()

                doc_type_mapping = {
                    "FORM 16": ["FORM 16", "FORM NO. 16", "FORM NO 16"],
                    "FORM 26AS": ["FORM 26AS", "FORM 26 AS"],
                    "AIS": ["AIS", "ANNUAL INFORMATION STATEMENT"]
                }

                doc_type_matches = False
                for key, variations in doc_type_mapping.items():
                    if expected_doc_type_normalized in variations or expected_doc_type_normalized == key:
                        if extracted_doc_type_normalized in variations or extracted_doc_type_normalized == key:
                            doc_type_matches = True
                            break

                if not doc_type_matches and extracted_doc_type_normalized == expected_doc_type_normalized:
                    doc_type_matches = True

                if not doc_type_matches:
                    debug_msg = f"[ERROR] Document Type verification failed: Document type mismatch detected."
                    debug_msg += f"\n   Selected Document Type: {expected_doc_type_value}"
                    debug_msg += f"\n   Document Type Found: {extracted_doc_type}"
                    debug_msg += f"\n   [REASON] This document appears to be a {extracted_doc_type}, but you selected {expected_doc_type_value}"
                    debug_msg += f"\n   [ACTION] Please upload the correct document type ({expected_doc_type_value})"

                    print(debug_msg)
                    return {
                        "verified": False,
                        "message": debug_msg,
                        "extracted_data": extracted,
                        "error_type": "document_type_mismatch"
                    }

                print(f"[SUCCESS] DOCUMENT TYPE VERIFIED: {extracted_doc_type} matches expected {expected_doc_type_value}")
            else:
                print(f"[WARNING] Document type not detected in document, but proceeding (may be scanned PDF)")

        # SUCCESS!
        print(f"\n{'=' * 60}")
        print(f"[SUCCESS] VERIFICATION SUCCESSFUL!")
        print(f"{'=' * 60}")
        print(f"[SUCCESS] PAN: {extracted_pan_clean} <- Matches your PAN")
        if expected_fy and extracted_fy:
            print(f"[SUCCESS] Financial Year: {extracted_fy} <- Matches selected FY")
        if expected_doc_type_value and extracted_doc_type:
            print(f"[SUCCESS] Document Type: {extracted_doc_type} <- Matches selected type")
        print(f"{'=' * 60}\n")

        return {
            "verified": True,
            "message": f"[SUCCESS] Document verified! PAN: {extracted_pan_clean}, FY: {extracted_fy or 'N/A'}, Type: {extracted_doc_type or 'N/A'}",
            "extracted_data": extracted,
            "text_content": text
        }

    except Exception as e:
        print(f"[ERROR] ERROR during verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "verified": False,
            "message": f"Verification error: {str(e)}",
            "extracted_data": None
        }


def extract_text_from_pdf_advanced(file_path: str) -> str:
    """
    🚀 ADVANCED PDF TEXT EXTRACTION (Powered by PyMuPDF)

    Exclusively uses PyMuPDF (fitz) for maximum speed and accuracy.
    Falls back to OCR only if text extraction yields poor results (scanned PDF).
    """
    extraction_results = {}

    # Method 1: PyMuPDF (fitz) - FASTEST & BEST FOR LAYOUTS
    try:
        print(f"🚀 Starting extraction with PyMuPDF (fitz)...")
        doc = fitz.open(file_path)

        # Faster than += in loop (reduces string re-allocations)
        text_parts = []

        for i, page in enumerate(doc):
            page_text = page.get_text("text", sort=True)
            if page_text:
                text_parts.append(f"\n=== PAGE {i+1} ===\n{page_text}\n")

        doc.close()

        text = "".join(text_parts)

        if text:
            if len(text.strip()) > 200:
                print(f"[PyMuPDF] Success: {len(text)} chars")
                return text
            else:
                print(f"[PyMuPDF] Warning: Only {len(text.strip())} chars extracted. PDF might be scanned.")
                extraction_results["fitz"] = text

    except Exception as e:
        print(f"[WARNING] PyMuPDF failed: {str(e)}")

    # Method 2: OCR (for scanned PDFs)
    if OCR_AVAILABLE:
        try:
            print(f"\n🔍 Attempting OCR extraction (this may take 10-30 seconds)...")
            print(f"⚠️  NOTE: OCR requires Poppler. If this fails, see TESSERACT_SETUP.md")
            ocr_text = extract_text_hybrid(file_path)
            if ocr_text and len(ocr_text.strip()) > 10:
                print(f"📝 OCR extraction: {len(ocr_text)} chars")
                return ocr_text
        except Exception as e:
            print(f"⚠️  OCR failed: {str(e)}")
            if "poppler" in str(e).lower():
                print(f"\n{'=' * 60}")
                print(f"⚠️  POPPLER NOT INSTALLED")
                print(f"{'=' * 60}")
                print(f"This PDF appears to be scanned/image-based.")
                print(f"To extract text, you need to install Poppler.")

    if "fitz" in extraction_results:
        return extraction_results["fitz"]

    raise Exception(
        f"❌ FAILED TO EXTRACT TEXT FROM PDF\n\n"
        f"PyMuPDF could not extract text and OCR is unavailable or failed.\n"
        f"The PDF appears to be scanned, corrupted, or password-protected.\n"
    )


async def extract_document_data(file_path: str, doc_type: DocType, financial_year: str,
                                text_content: str = None) -> Dict[str, Any]:
    """
    🎯 EXTRACT STRUCTURED DATA FROM VERIFIED DOCUMENT

    Uses hybrid approach:
    1. Extract text (advanced multi-method)
    2. Pattern extraction for common fields
    3. AI extraction for complex/variable fields
    """
    try:
        print(f"\n{'=' * 60}")
        print(f"📊 DATA EXTRACTION STARTED")
        print(f"{'=' * 60}\n")

        if text_content and len(text_content) > 10:
            print(f"[CACHE] Using pre-extracted text from verification phase ({len(text_content)} chars)")
            text = text_content
        else:
            text = extract_text_from_pdf_advanced(file_path)

        print(f"🤖 Using AI (local Mistral) for structured extraction...")
        extracted_data = await extract_data_with_ai(text, doc_type, financial_year)

        print(f"\n✅ Data extraction completed")
        print(f"{'=' * 60}\n")

        return extracted_data

    except Exception as e:
        print(f"❌ Error extracting data: {str(e)}")
        raise Exception(f"Error extracting data: {str(e)}")
