"""
Local OCR Service using Tesseract
Extracts text from PDF documents with word-level bounding boxes
100% offline - no cloud APIs needed
"""

import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
from typing import List, Dict, Any
import platform


# Configure Tesseract path based on OS
def get_tesseract_path():
    """Auto-detect Tesseract installation"""
    system = platform.system()

    if system == "Windows":
        # Common Windows installation paths
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        # If not found, assume it's in PATH
        return "tesseract"
    else:
        # Linux / macOS
        return "tesseract"


# Set Tesseract path
try:
    pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()
except Exception:
    pass  # Use system default


# Configure Poppler path for pdf2image
def get_poppler_path():
    """Auto-detect Poppler installation"""
    system = platform.system()

    if system == "Windows":
        possible_paths = [
            os.path.join(os.environ.get("USERPROFILE", ""), r"OCR_Tools\poppler-23.11.0\Library\bin"),
            os.path.join(os.environ.get("USERPROFILE", ""), r"OCR_Tools\poppler-24.08.0\Library\bin"),
            r"C:\Program Files\poppler\Library\bin",
            r"C:\poppler\Library\bin",
            r"C:\poppler\bin",
        ]

        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            ocr_tools_dir = os.path.join(user_profile, "OCR_Tools")
            if os.path.exists(ocr_tools_dir):
                for item in os.listdir(ocr_tools_dir):
                    poppler_dir = os.path.join(ocr_tools_dir, item)
                    if os.path.isdir(poppler_dir) and item.startswith("poppler-"):
                        lib_bin = os.path.join(poppler_dir, "Library", "bin")
                        if os.path.exists(os.path.join(lib_bin, "pdftoppm.exe")):
                            return lib_bin

                        bin_dir = os.path.join(poppler_dir, "bin")
                        if os.path.exists(os.path.join(bin_dir, "pdftoppm.exe")):
                            return bin_dir

        for path in possible_paths:
            if os.path.exists(os.path.join(path, "pdftoppm.exe")):
                return path

        return None

    # macOS (Apple Silicon Homebrew)
    if system == "Darwin":
        brew_path = "/opt/homebrew/bin"
        if os.path.exists(os.path.join(brew_path, "pdftoppm")):
            return brew_path
        return None

    # Linux
    return None


POPPLER_PATH = get_poppler_path()


def extract_text_with_ocr(file_path: str) -> Dict[str, Any]:
    """
    Extract text from PDF using OCR
    """
    try:
        print("=== OCR: Converting PDF to images... ===")

        if POPPLER_PATH:
            print(f"=== OCR: Using Poppler at: {POPPLER_PATH} ===")
            images = convert_from_path(
                file_path,
                dpi=300,
                fmt="png",
                poppler_path=POPPLER_PATH,
            )
        else:
            images = convert_from_path(
                file_path,
                dpi=300,
                fmt="png",
            )

        all_text = []
        pages_data = []

        ocr_config = "--oem 3 --psm 6"

        for page_num, image in enumerate(images, start=1):
            print(f"=== OCR: Processing page {page_num}/{len(images)}... ===")

            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config=ocr_config,
                lang="eng",
            )

            page_text = pytesseract.image_to_string(
                image,
                lang="eng",
                config=ocr_config,
            )
            all_text.append(page_text)

            words = []
            for i in range(len(ocr_data["text"])):
                text = ocr_data["text"][i].strip()
                if not text:
                    continue

                conf_raw = ocr_data["conf"][i]
                
                # Handle int or string confidence values - ROBUST FIX
                if isinstance(conf_raw, (int, float)):
                    confidence = float(conf_raw)
                elif isinstance(conf_raw, str):
                    # Check if string is a valid number (integer or float)
                    clean_conf = str(conf_raw).strip()
                    if clean_conf.replace('.', '', 1).isdigit() or (clean_conf.startswith('-') and clean_conf[1:].replace('.', '', 1).isdigit()):
                        confidence = float(clean_conf)
                    else:
                        confidence = -1.0
                else:
                    confidence = -1.0

                words.append({
                    "text": text,
                    "x": ocr_data["left"][i],
                    "y": ocr_data["top"][i],
                    "width": ocr_data["width"][i],
                    "height": ocr_data["height"][i],
                    "confidence": confidence,
                })

            pages_data.append({
                "page": page_num,
                "size": image.size,
                "words": words,
                "text": page_text,
            })

        full_text = "\n".join(all_text)

        print(f"=== OCR: Extracted {len(full_text)} characters from {len(images)} pages ===")

        return {
            "success": True,
            "raw_text": full_text,
            "pages": pages_data,
            "total_pages": len(images),
        }

    except Exception as e:
        print(f"=== OCR: Error - {str(e)} ===")
        return {
            "success": False,
            "error": str(e),
            "raw_text": "",
            "pages": [],
        }


def extract_text_hybrid(file_path: str) -> str:
    """
    Hybrid extraction: Try pdfplumber first, fall back to OCR
    """
    import pdfplumber

    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            if text and len(text.strip()) > 100:
                print(f"=== Using pdfplumber extraction ({len(text)} chars) ===")
                return text

    except Exception as e:
        print(f"=== pdfplumber failed: {str(e)}, falling back to OCR ===")

    print("=== Using OCR extraction (slower but works for scanned PDFs) ===")
    result = extract_text_with_ocr(file_path)

    if result["success"]:
        return result["raw_text"]

    raise Exception(f"OCR extraction failed: {result.get('error', 'Unknown error')}")
