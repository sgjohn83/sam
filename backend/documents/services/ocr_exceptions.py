class OCRProcessingError(Exception):
    """Gemini API call failed or pipeline error."""


class OCREmptyResultError(OCRProcessingError):
    """Gemini returned empty/unparseable response."""


class DocumentValidationError(Exception):
    """File validation failed."""


class FileSizeLimitError(DocumentValidationError):
    """File exceeds 5MB."""


class InvalidFileTypeError(DocumentValidationError):
    """File extension or MIME type not allowed."""
