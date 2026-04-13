from collections import Counter
from difflib import SequenceMatcher
from typing import Any
from uuid import UUID

from documents.models import Document
from students.models import StudentProfile


def _normalize_name(value: Any) -> str:
    if not value:
        return ""
    text = str(value).upper().strip()
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
    return " ".join("".join(cleaned).split())


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _extract_student_name_from_fields(document_type: str, fields: dict) -> str:
    if document_type == "aadhar":
        return str(fields.get("name") or "")
    if document_type in {"marksheet_10", "marksheet_12", "rank_card"}:
        return str(fields.get("candidate_name") or "")
    return str(fields.get("student_name") or "")


def cross_verify_student_name(student_id: UUID) -> dict:
    """
    Compare student_name extracted from all uploaded documents.
    """
    student = StudentProfile.objects.get(id=student_id)
    documents = Document.objects.filter(student=student).order_by("uploaded_at")

    names_found: dict[str, str] = {}
    normalized_pairs: list[tuple[str, str]] = []

    for doc in documents:
        latest = doc.get_latest_ocr_result()
        if not latest:
            continue
        raw_name = _extract_student_name_from_fields(doc.document_type, latest.extracted_fields)
        normalized = _normalize_name(raw_name)
        if not normalized:
            continue
        names_found[doc.document_type] = normalized
        normalized_pairs.append((doc.document_type, normalized))

    if not normalized_pairs:
        return {
            "names_found": {},
            "is_consistent": True,
            "mismatches": [],
            "canonical_name": "",
        }

    canonical_name = Counter(name for _, name in normalized_pairs).most_common(1)[0][0]
    mismatches = []
    for doc_type, name in normalized_pairs:
        # Fuzzy threshold: only flag significant differences.
        if _similarity(name, canonical_name) < 0.72:
            mismatches.append(doc_type)

    return {
        "names_found": names_found,
        "is_consistent": len(mismatches) == 0,
        "mismatches": mismatches,
        "canonical_name": canonical_name,
    }
