AP_BASE_HINT = (
    "Extract data from this Andhra Pradesh (AP) State document. "
    "Labels may be in Telugu, but extract data in English. "
    "If multiple values exist, pick the most relevant one."
)


def get_prompt(document_type: str) -> str:
    """Return extraction instruction prompt for the given document type."""
    if document_type == "aadhar":
        return (
            "Extract Aadhaar card details precisely according to the schema.\n"
            "RULES:\n"
            "- `aadhar_number`: 12-digit number, remove all spaces.\n"
            "- The address may be in Telugu script; transliterate it to English.\n"
            "- MOBILE NUMBER: Look for a 10-digit number next to 'Mobile:' "
            "in the address block or handwritten in margins.\n"
            "- `gender`: Male or Female.\n"
            + AP_BASE_HINT
        )
    if document_type == "marksheet_10":
        return (
            "Extract SSC (10th) certificate details precisely according to the schema.\n"
            "RULES:\n"
            "- 'Hall Ticket Number' is the primary identifier.\n"
            "- Identification marks are usually listed as '1.' and '2.'\n"
            "- Grade points are integers from 1 to 10.\n"
            "- Subject names may be abbreviated (e.g., FL = First Language, SL = Second Language).\n"
            "- `board` is typically 'AP SSC' or 'CBSE'.\n"
            "- Extract all subject grades and grade points.\n"
            "- GPA is the final grade point average.\n"
            + AP_BASE_HINT
        )
    if document_type == "marksheet_12":
        return (
            "Extract Intermediate (12th) certificate details precisely.\n"
            "RULES:\n"
            "- 'Hall Ticket Number' is the primary identifier.\n"
            "- Part-I is always English.\n"
            "- Part-II is second language.\n"
            "- Part-III contains 3 optional subjects.\n"
            "- Subjects are split into Part-I (English), Part-II (Second Language), "
            "Part-III (Optional subjects like Maths, Physics, Chemistry).\n"
            "- Practical marks may appear in a separate column; include them under `practical_marks`.\n"
            "- Extract year_1_marks and year_2_marks separately per subject.\n"
            "- grand_total is total marks across all subjects and years.\n"
            + AP_BASE_HINT
        )
    if document_type == "rank_card":
        return (
            "Extract EAMCET/EAPCET Rank Card details precisely.\n"
            "RULES:\n"
            "- `entrance_exam_name`: e.g. APEAPCET 2024.\n"
            "- `rank` is always a positive integer.\n"
            "- `hall_ticket_no` is typically 10 digits.\n"
            "- `caste_category`: e.g., BC_B, SC, ST, OC.\n"
            "- `local_area`: AU (Andhra University), SVU (Sri Venkateswara), OU (Osmania), NL (Non-Local).\n"
            + AP_BASE_HINT
        )
    return "Extract all visible text and fields from this document."
