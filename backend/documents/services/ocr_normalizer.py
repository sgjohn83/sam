import re
from typing import Any, Dict


AADHAAR_RE = re.compile(r"^\d{12}$")
PINCODE_RE = re.compile(r"\b\d{6}\b")
INDIAN_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _normalize_gender(value: Any) -> str:
    raw = _clean_text(value).lower()
    if raw in {"male", "m"}:
        return "Male"
    if raw in {"female", "f"}:
        return "Female"
    if raw:
        return "Other"
    return ""


def _normalize_aadhaar(value: Any) -> str:
    digits = re.sub(r"\D", "", _clean_text(value))
    return digits if AADHAAR_RE.match(digits) else ""


def _normalize_mobile(value: Any) -> str:
    digits = re.sub(r"\D", "", _clean_text(value))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return digits if INDIAN_MOBILE_RE.match(digits) else ""


def _extract_year(value: Any) -> str:
    raw = _clean_text(value)
    m = re.search(r"\b(19|20)\d{2}\b", raw)
    return m.group(0) if m else ""


def _normalize_date(value: Any) -> str:
    raw = _clean_text(value)
    if not raw:
        return ""
    # Keep string format for now; parser can be tightened later if needed.
    return raw


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    m = re.search(r"-?\d+", _clean_text(value).replace(",", ""))
    return int(m.group(0)) if m else None


def _parse_address(value: Any) -> Dict[str, str]:
    raw = _clean_text(value)
    if not raw:
        return {"street": "", "city": "", "state": "", "pincode": ""}

    pincode_match = PINCODE_RE.search(raw)
    pincode = pincode_match.group(0) if pincode_match else ""
    parts = [p.strip() for p in raw.split(",") if p.strip()]

    street = ""
    city = ""
    state = ""

    if len(parts) >= 3:
        street = ", ".join(parts[:-2])
        city = parts[-2]
        state = parts[-1].replace(pincode, "").strip(" -")
    elif len(parts) == 2:
        street = parts[0]
        state = parts[1].replace(pincode, "").strip(" -")
    elif len(parts) == 1:
        street = parts[0].replace(pincode, "").strip(" -")

    return {
        "street": street,
        "city": city,
        "state": state,
        "pincode": pincode,
    }


def normalize_aadhar(extracted_fields: dict) -> dict:
    """
    Normalize Aadhaar OCR output into application form fields.
    """
    data = extracted_fields or {}
    return {
        "student_name": _clean_text(data.get("name")),
        "date_of_birth": _normalize_date(data.get("date_of_birth")),
        "gender": _normalize_gender(data.get("gender")),
        "aadhar_number": _normalize_aadhaar(data.get("aadhar_number")),
        "address": _parse_address(data.get("address")),
        "mobile_number": _normalize_mobile(data.get("mobile")),
    }


def normalize_ssc(extracted_fields: dict) -> dict:
    """
    Normalize SSC output into application fields.
    subject_results => [{name, grade, grade_points}]
    """
    data = extracted_fields or {}
    raw_subjects = data.get("subject_results") or []
    normalized_subjects = []
    for item in raw_subjects:
        if not isinstance(item, dict):
            continue
        normalized_subjects.append(
            {
                "name": _clean_text(item.get("subject_name")),
                "grade": _clean_text(item.get("grade")),
                "grade_points": _safe_int(item.get("grade_points")) or 0,
            }
        )

    return {
        "student_name": _clean_text(data.get("candidate_name")),
        "father_name": _clean_text(data.get("father_name")),
        "ssc_hall_ticket": _clean_text(data.get("hall_ticket_no")),
        "ssc_school_name": _clean_text(data.get("school_name")),
        "ssc_gpa": data.get("gpa"),
        "ssc_year_of_passing": _extract_year(data.get("exam_month_year")),
        "ssc_subjects": normalized_subjects,
    }


def normalize_inter(extracted_fields: dict) -> dict:
    """
    Normalize intermediate output and merge subjects by first/second year.
    """
    data = extracted_fields or {}

    def normalize_inter_subject_list(values: Any) -> list[dict]:
        out = []
        if not isinstance(values, list):
            return out
        for item in values:
            if not isinstance(item, dict):
                continue
            out.append(
                {
                    "name": _clean_text(item.get("subject_name")),
                    "year_1_marks": _safe_int(item.get("year_1_marks")),
                    "year_2_marks": _safe_int(item.get("year_2_marks")),
                    "practical_marks": _safe_int(item.get("practical_marks")),
                    "total_marks": _safe_int(item.get("total_marks")),
                    "max_marks": _safe_int(item.get("max_marks")),
                }
            )
        return out

    all_subjects = []
    for key in ("part_1_subjects", "part_2_subjects", "part_3_subjects"):
        all_subjects.extend(normalize_inter_subject_list(data.get(key)))

    first_year = []
    second_year = []
    computed_total = 0
    for sub in all_subjects:
        y1 = sub.get("year_1_marks")
        y2 = sub.get("year_2_marks")
        if y1 is not None:
            first_year.append({"name": sub["name"], "marks": y1})
            computed_total += y1
        if y2 is not None:
            second_year.append({"name": sub["name"], "marks": y2})
            computed_total += y2

    explicit_total = _safe_int(data.get("grand_total"))
    inter_total_marks = explicit_total if explicit_total is not None else computed_total

    return {
        "student_name": _clean_text(data.get("candidate_name")),
        "inter_hall_ticket": _clean_text(data.get("hall_ticket_no")),
        "inter_college_name": _clean_text(data.get("college_name")),
        "inter_group": _clean_text(data.get("group_name")),
        "inter_total_marks": inter_total_marks,
        "inter_subjects": {
            "first_year": first_year,
            "second_year": second_year,
        },
        "inter_year_of_passing": _extract_year(data.get("exam_month_year")),
    }


def normalize_rank_card(extracted_fields: dict) -> dict:
    """
    Normalize rank card fields and map caste category to standard enum.
    """
    data = extracted_fields or {}
    raw_cat = _clean_text(data.get("caste_category")).upper()
    if raw_cat.startswith("SC"):
        category = "SC"
    elif raw_cat.startswith("ST"):
        category = "ST"
    elif raw_cat.startswith("BC") or raw_cat.startswith("OBC"):
        category = "OBC"
    else:
        category = "General"

    rank = _safe_int(data.get("rank"))
    category_rank = _safe_int(data.get("category_rank"))

    return {
        "student_name": _clean_text(data.get("candidate_name")),
        "entrance_exam_name": _clean_text(data.get("entrance_exam_name")),
        "rank_hall_ticket": _clean_text(data.get("hall_ticket_no")),
        "entrance_rank": rank if rank is not None and rank >= 0 else None,
        "category_rank": category_rank if category_rank is not None and category_rank >= 0 else None,
        "category": category,
    }


def normalize_document(document_type: str, extracted_fields: dict) -> dict:
    """
    Route to the correct normalizer for each document type.
    """
    if document_type == "aadhar":
        return normalize_aadhar(extracted_fields)
    if document_type == "marksheet_10":
        return normalize_ssc(extracted_fields)
    if document_type == "marksheet_12":
        return normalize_inter(extracted_fields)
    if document_type == "rank_card":
        return normalize_rank_card(extracted_fields)
    return extracted_fields or {}
