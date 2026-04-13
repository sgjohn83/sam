from rest_framework import serializers
from .models import Document, OCRResult

class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Document
        fields = ['document_type', 'file']


class DocumentReuploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class OCRResultSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRResult
        fields = ['overall_confidence', 'created_at']

class DocumentDetailSerializer(serializers.ModelSerializer):
    ocr_summary = OCRResultSummarySerializer(source='ocr_results.last', read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'document_type', 'status', 'upload_version', 'ocr_summary', 'rejection_reason']

class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'document_type', 'status', 'uploaded_at']


class OCRResultDetailSerializer(serializers.ModelSerializer):
    document_id = serializers.UUIDField(source="document.id", read_only=True)

    class Meta:
        model = OCRResult
        fields = [
            "document_id",
            "ocr_version",
            "raw_text",
            "extracted_fields",
            "confidence_scores",
            "overall_confidence",
            "processing_duration_ms",
            "llm_model_used",
            "created_at",
        ]


class OCRResultHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRResult
        fields = ["ocr_version", "overall_confidence", "created_at"]
