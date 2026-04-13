from uuid import UUID

from documents.models import Document
from students.models import StudentProfile

from .ocr_confidence import CONFIDENCE_THRESHOLDS, get_confidence_badge
from .ocr_cross_verify import cross_verify_student_name
from .ocr_normalizer import normalize_document


DOCUMENT_TYPES = ("aadhar", "marksheet_10", "marksheet_12", "rank_card")


def _default_documents_status() -> dict:
    return {
        "aadhar": {"uploaded": False, "status": None, "confidence": None},
        "marksheet_10": {"uploaded": False, "status": None, "confidence": None},
        "marksheet_12": {"uploaded": False, "status": None, "confidence": None},
        "rank_card": {"uploaded": False, "status": None, "confidence": None},
    }


def _default_profile_fields() -> dict:
    return {
        "full_name": "",
        "date_of_birth": "",
        "gender": "",
        "mobile_number": "",
        "aadhar_number": "",
        "address": {"street": "", "city": "", "state": "", "pincode": ""},
        "category": "",
        "domicile_state": "",
    }


def _default_academic_fields() -> dict:
    return {
        "ssc_hall_ticket": "",
        "ssc_school_name": "",
        "ssc_gpa": None,
        "ssc_year": None,
        "ssc_subjects": [],
        "inter_hall_ticket": "",
        "inter_college_name": "",
        "inter_group": "",
        "inter_total_marks": None,
        "inter_year": None,
        "inter_subjects": {"first_year": [], "second_year": []},
        "entrance_exam": "",
        "entrance_rank": None,
        "rank_hall_ticket": "",
    }


def generate_autofill_data(student_id: UUID) -> dict:
    """
    Collect latest OCR results from uploaded documents and generate unified autofill payload.
    """
    student = StudentProfile.objects.select_related("user").get(id=student_id)
    docs = Document.objects.filter(student=student)
    by_type = {doc.document_type: doc for doc in docs}

    profile_fields = _default_profile_fields()
    academic_fields = _default_academic_fields()
    documents_status = _default_documents_status()

    overall_scores = []
    low_confidence_fields = set()

    for doc_type in DOCUMENT_TYPES:
        doc = by_type.get(doc_type)
        if not doc:
            continue

        latest = doc.get_latest_ocr_result()
        documents_status[doc_type] = {
            "uploaded": True,
            "status": doc.status,
            "confidence": latest.overall_confidence if latest else None,
        }

        if not latest:
            continue

        overall_scores.append(latest.overall_confidence)
        normalized = normalize_document(doc_type, latest.extracted_fields)

        # Profile mapping
        if normalized.get("student_name"):
            profile_fields["full_name"] = normalized["student_name"]
        if normalized.get("date_of_birth"):
            profile_fields["date_of_birth"] = normalized["date_of_birth"]
        if normalized.get("gender"):
            profile_fields["gender"] = normalized["gender"]
        if normalized.get("mobile_number"):
            profile_fields["mobile_number"] = normalized["mobile_number"]
        if normalized.get("aadhar_number"):
            profile_fields["aadhar_number"] = normalized["aadhar_number"]
        if normalized.get("address"):
            profile_fields["address"] = normalized["address"]
        if normalized.get("category"):
            profile_fields["category"] = normalized["category"]

        # Academic mapping
        if normalized.get("ssc_hall_ticket"):
            academic_fields["ssc_hall_ticket"] = normalized["ssc_hall_ticket"]
        if normalized.get("ssc_school_name"):
            academic_fields["ssc_school_name"] = normalized["ssc_school_name"]
        if normalized.get("ssc_gpa") is not None:
            academic_fields["ssc_gpa"] = normalized["ssc_gpa"]
        if normalized.get("ssc_year_of_passing"):
            try:
                academic_fields["ssc_year"] = int(normalized["ssc_year_of_passing"])
            except (TypeError, ValueError):
                pass
        if normalized.get("ssc_subjects"):
            academic_fields["ssc_subjects"] = normalized["ssc_subjects"]

        if normalized.get("inter_hall_ticket"):
            academic_fields["inter_hall_ticket"] = normalized["inter_hall_ticket"]
        if normalized.get("inter_college_name"):
            academic_fields["inter_college_name"] = normalized["inter_college_name"]
        if normalized.get("inter_group"):
            academic_fields["inter_group"] = normalized["inter_group"]
        if normalized.get("inter_total_marks") is not None:
            academic_fields["inter_total_marks"] = normalized["inter_total_marks"]
        if normalized.get("inter_year_of_passing"):
            try:
                academic_fields["inter_year"] = int(normalized["inter_year_of_passing"])
            except (TypeError, ValueError):
                pass
        if normalized.get("inter_subjects"):
            academic_fields["inter_subjects"] = normalized["inter_subjects"]

        if normalized.get("entrance_exam_name"):
            academic_fields["entrance_exam"] = normalized["entrance_exam_name"]
        if normalized.get("entrance_rank") is not None:
            academic_fields["entrance_rank"] = normalized["entrance_rank"]
        if normalized.get("rank_hall_ticket"):
            academic_fields["rank_hall_ticket"] = normalized["rank_hall_ticket"]

        # Low-confidence fields collection
        for field_name, score in (latest.confidence_scores or {}).items():
            if float(score or 0.0) < CONFIDENCE_THRESHOLDS["medium"]:
                if field_name in {"mobile", "mobile_number"}:
                    low_confidence_fields.add("mobile_number")
                elif field_name == "address":
                    low_confidence_fields.add("address")
                else:
                    low_confidence_fields.add(field_name)

    # Fill defaults from StudentProfile if OCR misses values
    if not profile_fields["full_name"]:
        profile_fields["full_name"] = student.user.full_name or ""
    if not profile_fields["date_of_birth"] and student.date_of_birth:
        profile_fields["date_of_birth"] = student.date_of_birth.isoformat()
    if not profile_fields["gender"] and student.gender:
        profile_fields["gender"] = student.gender.title()
    if not profile_fields["mobile_number"]:
        profile_fields["mobile_number"] = student.mobile_number or ""
    if profile_fields["address"] == {"street": "", "city": "", "state": "", "pincode": ""}:
        profile_fields["address"] = student.address or profile_fields["address"]
    if not profile_fields["category"] and student.category:
        profile_fields["category"] = student.category.upper()
    if not profile_fields["domicile_state"]:
        profile_fields["domicile_state"] = student.domicile_state or ""

    overall_confidence = (
        round(sum(overall_scores) / len(overall_scores), 4) if overall_scores else 0.0
    )
    name_check = cross_verify_student_name(student_id)

    return {
        "profile_fields": profile_fields,
        "academic_fields": academic_fields,
        "confidence_summary": {
            "overall": overall_confidence,
            "badge": get_confidence_badge(overall_confidence),
            "low_confidence_fields": sorted(low_confidence_fields),
            "cross_verify": {
                "name_consistent": bool(name_check.get("is_consistent", True)),
                "mismatches": name_check.get("mismatches", []),
            },
        },
        "documents_status": documents_status,
    }
