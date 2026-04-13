import os
import time
import logging
import re
from uuid import UUID

import PIL.Image
import google.genai as genai
from google.genai import types
from django.conf import settings

from documents.models import Document, OCRResult, DocumentStatus
from verification.services import create_field_verifications
from .ocr_exceptions import OCRProcessingError, OCREmptyResultError
from .ocr_schemas import SCHEMA_MAP
from .ocr_prompts import get_prompt
from .ocr_validators import parse_date, validate_indian_mobile
from .ocr_utils import (
    pdf_to_image_paths,
    parse_json_response,
    clean_parsed_fields,
    cleanup_temp_images,
)

logger = logging.getLogger("ocr")
SLOW_OCR_THRESHOLD_MS = 15000


# ---- Gemini Client (singleton) ----
_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise OCRProcessingError("GEMINI_API_KEY not configured")
        _client = genai.Client(api_key=api_key)
    return _client


# ---- Gemini VLM Call ----
def _call_gemini(contents: list, response_schema=None) -> str:
    """Call Gemini VLM. Returns raw JSON text or empty string on failure."""
    try:
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
        resp = _get_client().models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        return getattr(resp, "text", "") or ""
    except Exception:
        logger.exception("Gemini VLM call failed")
        return ""


# ---- Confidence Scoring ----
def _compute_confidence(extracted: dict) -> tuple[dict, float]:
    """
    Compute per-field confidence scores using field-aware rules.
    Returns (confidence_scores, overall_confidence).
    """
    def _text(value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _digit_count(value) -> int:
        return len(re.sub(r"\D", "", _text(value)))

    def _try_int(value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        m = re.search(r"-?\d+", str(value).replace(",", ""))
        return int(m.group(0)) if m else None

    def _score_hall_ticket(value) -> float:
        raw = _text(value)
        if not raw:
            return 0.0
        # Expected broadly alphanumeric IDs with optional '-' or '/'.
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9/-]{4,24}", raw):
            return 0.95
        return 0.50

    def _score_subject_results(value) -> float:
        if not isinstance(value, list) or len(value) == 0:
            return 0.0
        if len(value) >= 5:
            return 0.95
        return 0.70

    scores = {}
    for key, value in extracted.items():
        key_lower = key.lower()
        raw_text = _text(value)

        if key_lower in {"aadhar_number", "aadhaar_number"}:
            if not raw_text:
                scores[key] = 0.0
            else:
                digits = _digit_count(value)
                if digits == 12:
                    scores[key] = 0.95
                elif 11 <= digits <= 13:
                    scores[key] = 0.50
                else:
                    scores[key] = 0.0

        elif key_lower in {"mobile", "mobile_number"}:
            if not raw_text:
                scores[key] = 0.0
            else:
                scores[key] = 0.95 if validate_indian_mobile(raw_text) else 0.30

        elif key_lower == "date_of_birth":
            if not raw_text:
                scores[key] = 0.0
            else:
                scores[key] = 0.95 if parse_date(raw_text) is not None else 0.50

        elif key_lower in {"hall_ticket_no", "ssc_hall_ticket", "inter_hall_ticket", "rank_hall_ticket"}:
            scores[key] = _score_hall_ticket(value)

        elif key_lower in {"rank", "entrance_rank"}:
            if not raw_text:
                scores[key] = 0.0
            else:
                rank_val = _try_int(value)
                scores[key] = 0.95 if (rank_val is not None and rank_val > 0) else 0.50

        elif key_lower == "subject_results":
            scores[key] = _score_subject_results(value)

        elif key_lower in {"gpa", "ssc_gpa"}:
            if value is None or raw_text == "":
                scores[key] = 0.0
            else:
                try:
                    gpa_val = float(value)
                except (TypeError, ValueError):
                    gpa_val = None
                if gpa_val is not None and 0 <= gpa_val <= 10:
                    scores[key] = 0.95
                else:
                    scores[key] = 0.50

        elif key_lower in {"grand_total", "inter_total_marks"}:
            if value is None or raw_text == "":
                scores[key] = 0.0
            else:
                marks_val = _try_int(value)
                if marks_val is not None and 0 <= marks_val <= 2000:
                    scores[key] = 0.95
                else:
                    scores[key] = 0.50

        elif isinstance(value, str):
            length = len(raw_text)
            if length == 0:
                scores[key] = 0.0
            elif length <= 2:
                scores[key] = 0.50
            else:
                scores[key] = 0.95

        elif isinstance(value, list):
            scores[key] = 0.95 if len(value) > 0 else 0.0

        elif isinstance(value, dict):
            scores[key] = 0.95 if value else 0.0

        elif isinstance(value, (int, float)):
            scores[key] = 0.95

        else:
            scores[key] = 0.0

    values = list(scores.values())
    overall = sum(values) / len(values) if values else 0.0
    return scores, round(overall, 4)


# ---- Main Pipeline ----
def process_document(document_id: UUID) -> OCRResult:
    """
    Process a document through Gemini VLM OCR pipeline.
    """
    start = time.perf_counter()
    document = Document.objects.get(id=document_id)
    file_path = os.path.join(settings.MEDIA_ROOT, document.file_path)

    if not os.path.exists(file_path):
        logger.error("Document file not found: document=%s path=%s", document_id, file_path)
        raise OCRProcessingError(f"File not found: {file_path}")

    suffix = os.path.splitext(file_path)[1].lower()
    temp_images = []
    image_paths = []

    try:
        # Step 1: Prepare images
        if suffix == ".pdf":
            image_paths = pdf_to_image_paths(file_path, dpi=200)
            temp_images = image_paths  # Track for cleanup
            logger.info(
                "Prepared multi-page PDF for OCR: document=%s pages=%d",
                document_id,
                len(image_paths),
            )
        else:
            image_paths = [file_path]

        # Step 2: Build prompt
        prompt_text = get_prompt(document.document_type)
        full_prompt = (
            f"{prompt_text}\n\n"
            "IMPORTANT:\n"
            "1. Provide a full text transcript of the document in the 'transcript' field.\n"
            "2. Extract all other fields precisely as per the schema.\n"
            "3. The document may be rotated or skewed; extract data regardless of orientation.\n"
            "4. If the same field appears on multiple pages, use the value from the page with clearest print.\n"
        )

        # Step 3: Build contents (prompt + images)
        contents = [full_prompt]
        opened_images = []

        try:
            for img_path in image_paths:
                img = PIL.Image.open(img_path)
                opened_images.append(img)
                if img.width < 500:
                    logger.warning(
                        "Low-resolution image detected (<500px width): document=%s image=%s width=%d",
                        document_id,
                        img_path,
                        img.width,
                    )
                contents.append(img)

            # Step 4: Select schema and call Gemini
            response_schema = SCHEMA_MAP.get(document.document_type)
            raw_response = _call_gemini(contents, response_schema=response_schema)

        finally:
            for img in opened_images:
                try:
                    img.close()
                except Exception:
                    pass

        # Step 5: Parse response
        duration_ms = int((time.perf_counter() - start) * 1000)

        if not raw_response:
            logger.warning(
                "Empty Gemini response for document %s (type=%s, duration=%dms)",
                document_id,
                document.document_type,
                duration_ms,
            )
            OCRResult.objects.create(
                document=document,
                raw_text="",
                extracted_fields={},
                confidence_scores={},
                overall_confidence=0.0,
                processing_duration_ms=duration_ms,
                ocr_version=document.upload_version,
                llm_model_used=settings.GEMINI_MODEL,
            )
            raise OCREmptyResultError(f"Empty response for document {document_id}")

        parsed = parse_json_response(raw_response)
        parsed = clean_parsed_fields(parsed)
        if not parsed:
            logger.warning(
                "Unparseable Gemini response for document %s (type=%s, duration=%dms)",
                document_id,
                document.document_type,
                duration_ms,
            )
            OCRResult.objects.create(
                document=document,
                raw_text="",
                extracted_fields={},
                confidence_scores={},
                overall_confidence=0.0,
                processing_duration_ms=duration_ms,
                ocr_version=document.upload_version,
                llm_model_used=settings.GEMINI_MODEL,
            )
            raise OCREmptyResultError(f"Unparseable response for document {document_id}")

        # Step 6: Separate transcript (raw OCR text) from extracted fields
        raw_text = parsed.pop("transcript", "")
        extracted_fields = parsed

        # Step 7: Compute confidence
        confidence_scores, overall_confidence = _compute_confidence(extracted_fields)

        # Step 8: Log performance
        if duration_ms > SLOW_OCR_THRESHOLD_MS:
            logger.warning(
                "Slow OCR: document %s took %dms (threshold: 15000ms)",
                document_id,
                duration_ms,
            )
        else:
            logger.info(
                "OCR completed: document=%s type=%s confidence=%.2f duration=%dms",
                document_id,
                document.document_type,
                overall_confidence,
                duration_ms,
            )

        # Step 9: Save OCRResult
        ocr_result = OCRResult.objects.create(
            document=document,
            raw_text=raw_text[:5000],  # Cap raw text length
            extracted_fields=extracted_fields,
            confidence_scores=confidence_scores,
            overall_confidence=overall_confidence,
            processing_duration_ms=duration_ms,
            ocr_version=document.upload_version,
            llm_model_used=settings.GEMINI_MODEL,
        )

        # Step 10: Create field verification records for each extracted field
        try:
            create_field_verifications(ocr_result)
        except Exception as e:
            logger.error("Failed to create field verifications for OCR result %s: %s", ocr_result.id, str(e))
            # Don't fail the entire OCR process if field verification creation fails

        # Step 11: Update document status
        document.status = DocumentStatus.EXTRACTED
        document.save(update_fields=["status"])

        return ocr_result

    except (OCRProcessingError, OCREmptyResultError):
        raise
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "OCR pipeline failed: document=%s type=%s duration=%dms error=%s",
            document_id,
            document.document_type,
            duration_ms,
            str(e),
        )
        # Keep status as 'processing' so it can be retried
        raise OCRProcessingError(f"Pipeline failed for document {document_id}: {e}")
    finally:
        cleanup_temp_images(temp_images)
