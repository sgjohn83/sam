import os
import uuid
from django.conf import settings
from .services.ocr_exceptions import FileSizeLimitError, InvalidFileTypeError

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'application/pdf'}

def validate_file(file):
    # Check size (configurable)
    if file.size > settings.MAX_UPLOAD_SIZE:
        raise FileSizeLimitError("File size exceeds 5MB")
    
    # Check extension and mime
    ext = os.path.splitext(file.name)[1].lower()
    allowed_exts = {e.lower() for e in settings.ALLOWED_UPLOAD_EXTENSIONS}
    if ext not in allowed_exts:
        raise InvalidFileTypeError("Only JPG, PNG, and PDF files are allowed")
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError("Only JPG, PNG, and PDF files are allowed")

def generate_file_path(student_id, document_type, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"documents/{student_id}/{document_type}/{uuid.uuid4()}{ext}"

def save_document(student_id, document_type, file):
    validate_file(file)
    path = generate_file_path(student_id, document_type, file.name)
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
            
    return path
