from rest_framework import serializers
from .models import AcademicYear, Branch, SeatMatrix, QuotaType


class SeatMatrixSerializer(serializers.ModelSerializer):
    branch_id = serializers.UUIDField(source="branch.id", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    quota_label = serializers.CharField(source="get_quota_display", read_only=True)
    available = serializers.SerializerMethodField()

    class Meta:
        model = SeatMatrix
        fields = [
            "id",
            "branch_id",
            "branch_name",
            "branch_code",
            "quota",
            "quota_label",
            "total_seats",
            "allocated_seats",
            "available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "allocated_seats", "created_at", "updated_at"]

    def get_available(self, obj):
        return max(obj.total_seats - obj.allocated_seats, 0)


class SeatMatrixUpsertSerializer(serializers.ModelSerializer):
    branch_id = serializers.UUIDField()
    quota = serializers.ChoiceField(choices=QuotaType.choices)
    total_seats = serializers.IntegerField(min_value=0)

    class Meta:
        model = SeatMatrix
        fields = ["branch_id", "quota", "total_seats"]

    def validate(self, attrs):
        branch_id = attrs.get("branch_id")
        quota = attrs.get("quota")
        total_seats = attrs.get("total_seats")

        try:
            branch = Branch.objects.get(id=branch_id, is_active=True)
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"branch_id": "Invalid or inactive branch"})

        attrs["branch"] = branch
        del attrs["branch_id"]

        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            raise serializers.ValidationError({"error": "No current academic year found"})

        attrs["academic_year"] = current_year

        existing = SeatMatrix.objects.filter(
            branch=branch,
            academic_year=current_year,
            quota=quota,
        ).first()

        if existing and total_seats < existing.allocated_seats:
            raise serializers.ValidationError({
                "total_seats": f"Cannot reduce below allocated seats ({existing.allocated_seats})"
            })

        return attrs


class SeatMatrixBulkUpsertSerializer(serializers.Serializer):
    items = SeatMatrixUpsertSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item required")

        if len(items) > 200:
            raise serializers.ValidationError("Maximum 200 items allowed")

        return items