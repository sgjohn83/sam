import os
import re
import ast
import json
import logging
import tempfile
from typing import Any, Dict, List

logger = logging.getLogger("ocr")

# --- PDF support ---
try:
    import fitz  # PyMuPDF

    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

try:
    from pdf2image import convert_from_path

    _HAS_PDF2IMAGE = True
except ImportError:
    _HAS_PDF2IMAGE = False


def pdf_to_image_paths(pdf_path: str, dpi: int = 200) -> List[str]:
    """Convert PDF to PNG images. Tries PyMuPDF first, pdf2image fallback."""
    images: List[str] = []

    if _HAS_FITZ:
        try:
            doc = fitz.open(pdf_path)
            for i in range(doc.page_count):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=dpi, alpha=False)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                pix.save(tmp.name)
                tmp.close()
                images.append(tmp.name)
            doc.close()
            return images
        except Exception as e:
            logger.warning("PyMuPDF failed: %s", e)

    if _HAS_PDF2IMAGE:
        try:
            pil_images = convert_from_path(pdf_path, dpi=dpi)
            for img in pil_images:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img.save(tmp.name, format="PNG")
                tmp.close()
                images.append(tmp.name)
            return images
        except Exception as e:
            logger.error("pdf2image failed: %s", e)

    logger.error("PDF conversion failed for file: %s", pdf_path)
    raise RuntimeError("PDF processing requires PyMuPDF or pdf2image+poppler.")


def parse_json_response(raw_text: str) -> Dict[str, Any]:
    """Extract JSON from Gemini response. Strips code fences, tries multiple parsers."""
    if not raw_text:
        return {}

    text = raw_text.strip()
    # Remove ```json / ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.IGNORECASE).strip()

    # Direct JSON parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Find first {...} block
    match = re.search(r"({[\s\S]*})", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Fallback: ast.literal_eval
    try:
        return ast.literal_eval(text)
    except Exception:
        return {}


def parse_json_from_gemini(raw_text: str) -> Dict[str, Any]:
    """Backward-compatible alias used by current OCR service."""
    return parse_json_response(raw_text)


def sanitize_english(text: Any) -> Any:
    """Keep only ASCII-safe characters."""
    if not isinstance(text, str):
        return text
    return re.sub(r"[^A-Za-z0-9 ,.\-:/()\n'\"&]", " ", text).strip()


def clean_parsed_fields(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Replace None values with empty strings, sanitize string values."""
    for k, v in list(parsed.items()):
        if v is None:
            parsed[k] = ""
        elif isinstance(v, str):
            parsed[k] = sanitize_english(v)
    return parsed


def cleanup_temp_images(image_paths: List[str]):
    """Remove temporary image files created from PDF conversion."""
    for p in image_paths:
        try:
            os.remove(p)
        except OSError:
            pass
