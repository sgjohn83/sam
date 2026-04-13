import re
from datetime import date, datetime
from typing import Any, Iterable


AADHAAR_RE = re.compile(r"^\d{12}$")
INDIAN_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")
PINCODE_RE = re.compile(r"^\d{6}$")
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def safe_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    m = re.search(r"-?\d+", clean_text(value).replace(",", ""))
    return int(m.group(0)) if m else 0


def validate_aadhar_number(num: str) -> str:
    """
    Strip spaces/non-digits, verify exactly 12 digits, return clean string.
    """
    digits = re.sub(r"\D", "", clean_text(num))
    return digits if AADHAAR_RE.match(digits) else ""


def normalize_aadhaar(value: Any) -> str:
    return validate_aadhar_number(clean_text(value))


def is_valid_aadhaar(value: Any) -> bool:
    return bool(validate_aadhar_number(clean_text(value)))


def validate_indian_mobile(mobile: str) -> str:
    """
    Strip +91/0 prefix and separators, validate 10-digit Indian mobile.
    """
    digits = re.sub(r"\D", "", clean_text(mobile))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if INDIAN_MOBILE_RE.match(digits) else ""


def normalize_indian_mobile(value: Any) -> str:
    return validate_indian_mobile(clean_text(value))


def is_valid_indian_mobile(value: Any) -> bool:
    return bool(validate_indian_mobile(clean_text(value)))


def normalize_gender(value: Any) -> str:
    raw = clean_text(value).lower()
    if raw in {"male", "m"}:
        return "Male"
    if raw in {"female", "f"}:
        return "Female"
    if raw in {"other", "o", "transgender"}:
        return "Other"
    return ""


def extract_year(value: Any) -> str:
    m = YEAR_RE.search(clean_text(value))
    return m.group(0) if m else ""


def parse_date(date_str: str) -> date | None:
    """
    Try multiple formats and return date object.
    """
    raw = clean_text(date_str)
    if not raw:
        return None
    candidates = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_year_from_exam(exam_str: str) -> int | None:
    """
    Extract four-digit year from exam string.
    """
    m = YEAR_RE.search(clean_text(exam_str))
    return int(m.group(0)) if m else None


def is_valid_pincode(value: Any) -> bool:
    return bool(PINCODE_RE.match(clean_text(value)))


def parse_address(address_str: str) -> dict:
    """
    Best-effort split into {street, city, state, pincode}.
    """
    raw = clean_text(address_str)
    if not raw:
        return {"street": "", "city": "", "state": "", "pincode": ""}

    pincode_match = re.search(r"\b\d{6}\b", raw)
    pincode = pincode_match.group(0) if pincode_match else ""

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    street = ""
    city = ""
    state = ""

    if len(parts) >= 3:
        street = ", ".join(parts[:-2])
        city = parts[-2]
        state = parts[-1]
    elif len(parts) == 2:
        street = parts[0]
        state = parts[1]
    elif len(parts) == 1:
        street = parts[0]

    state = state.replace(pincode, "").strip(" -")
    street = street.replace(pincode, "").strip(" -")

    return {
        "street": street,
        "city": city,
        "state": state,
        "pincode": pincode,
    }


def map_category(caste: str) -> str:
    """
    Map AP caste codes to standard enum.
    BC_A/BC_B/BC_C/BC_D/BC_E -> OBC, SC -> SC, ST -> ST, OC -> General.
    """
    value = clean_text(caste)
    raw = clean_text(value).upper()
    if raw.startswith("SC"):
        return "SC"
    if raw.startswith("ST"):
        return "ST"
    if raw in {"BC_A", "BC_B", "BC_C", "BC_D", "BC_E"} or raw.startswith("BC") or raw.startswith("OBC"):
        return "OBC"
    if raw == "OC":
        return "General"
    return "General"


def validate_rank(value: Any) -> int | None:
    rank = safe_int(value)
    if rank < 0:
        return None
    return rank


def normalize_ssc_subjects(items: Any) -> list[dict]:
    out = []
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes, dict)):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": clean_text(item.get("subject_name")),
                "grade": clean_text(item.get("grade")),
                "grade_points": safe_int(item.get("grade_points")),
            }
        )
    return out


def normalize_inter_subjects(items: Any) -> list[dict]:
    out = []
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes, dict)):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": clean_text(item.get("subject_name")),
                "year_1_marks": safe_int(item.get("year_1_marks")) or None,
                "year_2_marks": safe_int(item.get("year_2_marks")) or None,
                "practical_marks": safe_int(item.get("practical_marks")) or None,
                "total_marks": safe_int(item.get("total_marks")) or None,
                "max_marks": safe_int(item.get("max_marks")) or None,
            }
        )
    return out
