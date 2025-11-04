# services/layout_ocr.py
# Python 3.9-compatible (no | types)

import os
from typing import List, Dict, Any, Tuple
import pytesseract
from pdf2image import convert_from_path
from core.config import TESSERACT_PATH, POPPLER_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def ocr_words_from_pdf(
    pdf_path: str,
    dpi: int = 300,
    max_pages: int = 5
) -> List[Dict[str, Any]]:
    """
    OCR the first few pages of the PDF into a list:
    [
      {
        "page": 1,
        "words": [
          {"text": "...", "left": x, "top": y, "width": w, "height": h, "conf": 85}
        ],
        "size": {"width": img_w, "height": img_h}
      },
      ...
    ]
    """
    pages_data: List[Dict[str, Any]] = []
    try:
        pages = convert_from_path(
            pdf_path, dpi=dpi, first_page=1, last_page=max_pages, poppler_path=POPPLER_PATH
        )
    except Exception as e:
        print(f"⚠️ convert_from_path failed for {pdf_path}: {e}")
        return pages_data

    for idx, img in enumerate(pages, start=1):
        try:
            od = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            words = []
            for i in range(len(od["text"])):
                txt = od["text"][i].strip()
                if not txt:
                    continue
                try:
                    conf = float(od["conf"][i])
                except:
                    conf = -1.0
                words.append({
                    "text": txt,
                    "left": int(od["left"][i]),
                    "top": int(od["top"][i]),
                    "width": int(od["width"][i]),
                    "height": int(od["height"][i]),
                    "conf": conf
                })
            pages_data.append({
                "page": idx,
                "words": words,
                "size": {"width": img.width, "height": img.height}
            })
        except Exception as e:
            print(f"⚠️ OCR failed on page {idx}: {e}")
            continue

    return pages_data


def words_to_lines(words: List[Dict[str, Any]], y_tol: int = 8) -> List[List[Dict[str, Any]]]:
    """
    Group words into lines by Y proximity (simple, fast).
    """
    if not words:
        return []
    # sort by Y then X
    words_sorted = sorted(words, key=lambda w: (w["top"], w["left"]))
    lines: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    last_y = None

    for w in words_sorted:
        if last_y is None:
            current = [w]
            last_y = w["top"]
        else:
            if abs(w["top"] - last_y) <= y_tol:
                current.append(w)
                last_y = (last_y + w["top"]) // 2
            else:
                lines.append(sorted(current, key=lambda x: x["left"]))
                current = [w]
                last_y = w["top"]

    if current:
        lines.append(sorted(current, key=lambda x: x["left"]))

    return lines


def lines_to_text(lines: List[List[Dict[str, Any]]]) -> List[str]:
    """
    Convert grouped lines to plain strings, left->right.
    """
    out = []
    for line in lines:
        out.append(" ".join([w["text"] for w in line]))
    return out


def detect_tables(lines: List[List[Dict[str, Any]]], col_gaps: int = 60) -> List[Dict[str, Any]]:
    """
    A lightweight table detector: we approximate columns by left positions
    and group rows with similar column anchors.
    Good enough for AIS lists or 26AS rows (sr no, amount, status).
    Returns:
      [{"rows":[["Sr. No.","Dividend Amount","Status"],["1","102","Matched"], ...]}]
    """
    if not lines:
        return []
    # Build column anchors by scanning the widest line
    widest = max(lines, key=lambda l: len(l))
    anchors = [w["left"] for w in widest]
    anchors = sorted(anchors)

    def map_to_cols(line):
        row = []
        for w in line:
            # find nearest anchor
            best_i = 0
            best_d = 10**9
            for i, a in enumerate(anchors):
                d = abs(w["left"] - a)
                if d < best_d:
                    best_d = d
                    best_i = i
            while len(row) <= best_i:
                row.append("")
            row[best_i] = (row[best_i] + " " + w["text"]).strip()
        return row

    # map each line to row
    rows = [map_to_cols(line) for line in lines if line]
    # cleanup empty-only rows
    rows = [r for r in rows if any(cell for cell in r)]
    if not rows:
        return []
    return [{"rows": rows}]
