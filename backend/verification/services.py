from django.core.cache import cache
from admissions.models import Application
from documents.models import Document, OCRResult
from .models import FieldVerification, FieldVerificationState
from django.utils import timezone
import uuid

def compute_application_confidence(application_id: uuid.UUID) -> dict:
    """
    Aggregate OCR confidence across all documents for an application.
    Application overall = average of all document confidences.
    """
    cache_key = f"verification:confidence:{application_id}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    try:
        application = Application.objects.select_related('student').get(id=application_id)
    except Application.DoesNotExist:
        return None

    # Get all documents for the student
    docs = application.student.documents.all()
    doc_results = []
    conf_sum = 0
    doc_count = 0

    for doc in docs:
        ocr = doc.get_latest_ocr_result()
        conf = ocr.overall_confidence if ocr else 0.0
        
        # Badge for individual document
        badge_level = "low"
        if conf >= 0.90:
            badge_level = "high"
        elif conf >= 0.70:
            badge_level = "medium"

        doc_results.append({
            "type": doc.document_type,
            "confidence": round(conf, 2),
            "badge": badge_level
        })
        conf_sum += conf
        doc_count += 1

    overall_conf = conf_sum / doc_count if doc_count > 0 else 0.0
    
    # Badge for overall application
    overall_badge = {"level": "low", "color": "red"}
    if overall_conf >= 0.90:
        overall_badge = {"level": "high", "color": "green"}
    elif overall_conf >= 0.70:
        overall_badge = {"level": "medium", "color": "yellow"}

    result = {
        "overall_confidence": round(overall_conf, 2),
        "documents": doc_results,
        "badge": overall_badge
    }

    # Cache for 60 seconds
    cache.set(cache_key, result, timeout=60)
    return result


def invalidate_application_confidence(application_id: uuid.UUID):
    """
    Invalidate the cached confidence score for an application.
    """
    cache.delete(f"verification:confidence:{application_id}")


def compute_cross_verification(application_id: uuid.UUID) -> dict:
    """
    Compute cross verification consistency across documents for an application.
    Returns:
        {
            "name_consistent": bool,
            "names_found": {
                "aadhar": str,
                "marksheet_10": str,
                "marksheet_12": str,
                "rank_card": str,
            },
            "mismatches": list[str]
        }
    """
    try:
        application = Application.objects.select_related('student').get(id=application_id)
    except Application.DoesNotExist:
        return None

    documents = application.student.documents.all()
    names_found = {}
    mismatches = []

    # Map document_type to field name for student name
    # Assuming extracted_fields contain 'name' field
    for doc in documents:
        ocr = doc.get_latest_ocr_result()
        if not ocr or not ocr.extracted_fields:
            continue
        name = ocr.extracted_fields.get('name')
        if name:
            names_found[doc.document_type] = name

    # Check consistency
    unique_names = set(names_found.values())
    name_consistent = len(unique_names) <= 1

    if not name_consistent:
        mismatches = list(unique_names)

    return {
        'name_consistent': name_consistent,
        'names_found': names_found,
        'mismatches': mismatches
    }


def compute_verification_progress(application_id: uuid.UUID) -> dict:
    """
    Compute verification progress for an application.
    Returns:
        {
            "total_documents": int,
            "verified_count": int,
            "rejected_count": int,
            "pending_count": int,
            "can_lock": bool
        }
    """
    try:
        application = Application.objects.select_related('student').get(id=application_id)
    except Application.DoesNotExist:
        return None

    documents = application.student.documents.all()
    total = documents.count()
    verified = documents.filter(status='verified').count()
    rejected = documents.filter(status='rejected').count()
    pending = total - verified - rejected

    # Determine if can lock (all documents verified or rejected)
    can_lock = verified + rejected == total

    return {
        'total_documents': total,
        'verified_count': verified,
        'rejected_count': rejected,
        'pending_count': pending,
        'can_lock': can_lock
    }


def compute_field_states(ocr_result_id: uuid.UUID) -> dict:
    """
    Compute field states for an OCR result based on FieldVerification.
    Returns dict mapping field_name -> state ('pending', 'verified', 'rejected')
    """
    ocr_result = OCRResult.objects.filter(id=ocr_result_id).first()
    if not ocr_result or not ocr_result.extracted_fields:
        return {}

    # Get field verifications for this OCR result
    field_verifications = FieldVerification.objects.filter(
        ocr_result=ocr_result
    ).only('field_name', 'state')

    # Build mapping
    state_map = {}
    for fv in field_verifications:
        # Map FieldVerificationState to simplified state
        if fv.state in [FieldVerificationState.APPROVED, FieldVerificationState.EDITED]:
            state_map[fv.field_name] = 'verified'
        elif fv.state == FieldVerificationState.FLAGGED:
            state_map[fv.field_name] = 'rejected'
        else:
            state_map[fv.field_name] = 'pending'

    # For fields without verification records, default to pending
    for field_name in ocr_result.extracted_fields.keys():
        if field_name not in state_map:
            state_map[field_name] = 'pending'

    return state_map


def create_field_verifications(ocr_result: OCRResult):
    """
    Auto-create FieldVerification rows for each extracted field.
    """
    for field_name, value in ocr_result.extracted_fields.items():
        FieldVerification.objects.create(
            document=ocr_result.document,
            ocr_result=ocr_result,
            field_name=field_name,
            original_value=str(value) if value is not None else '',
            current_value=str(value) if value is not None else '',
            confidence=ocr_result.confidence_scores.get(field_name, 0.0),
            state=FieldVerificationState.PENDING,
        )
