from rest_framework import serializers
from .models import AgentProfile, CommissionRecord
from students.models import StudentProfile, StudentCategory


class AgentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            'id',
            'email',
            'full_name',
            'agency_name',
            'contact_phone',
            'address',
            'pan_number',
            'bank_account_name',
            'bank_account_number',
            'bank_ifsc',
            'commission_rate',
            'is_verified',
            'is_active',
            'total_students_referred',
            'total_commission_earned',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'full_name',
            'commission_rate',
            'is_verified',
            'is_active',
            'total_students_referred',
            'total_commission_earned',
            'created_at',
            'updated_at',
        ]


class CommissionRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.full_name', read_only=True)
    agent_name = serializers.CharField(source='agent.agency_name', read_only=True)
    application_number = serializers.CharField(source='application.application_number', read_only=True)
    branch_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CommissionRecord
        fields = [
            'id',
            'student_name',
            'agent_name',
            'application_number',
            'branch_name',
            'fee_amount',
            'commission_rate',
            'commission_amount',
            'status',
            'status_display',
            'notes',
            'approved_at',
            'paid_at',
            'payment_reference',
            'created_at',
        ]
        read_only_fields = fields

    def get_branch_name(self, obj):
        branch = getattr(obj.application, 'allocated_branch', None)
        return branch.name if branch else None


class AgentStudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    mobile_number = serializers.CharField(source='mobile_number', read_only=True)
    application_number = serializers.CharField(source='application.application_number', read_only=True)
    status = serializers.CharField(source='application.status', read_only=True)
    branch_name = serializers.CharField(source='application.allocated_branch.name', read_only=True)
    submitted_at = serializers.DateTimeField(source='application.submitted_at', read_only=True)
    admitted_at = serializers.DateTimeField(source='application.admitted_at', read_only=True)
    fee_amount = serializers.DecimalField(source='application.fee_amount', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'full_name', 'email', 'mobile_number', 'application_number',
            'status', 'branch_name', 'submitted_at', 'admitted_at', 'fee_amount'
        ]


class AgentRegisterStudentSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    category = serializers.ChoiceField(choices=StudentCategory.choices, required=False)


class AgentStudentDetailSerializer(AgentStudentSerializer):
    status_timeline = serializers.SerializerMethodField()
    commission_record = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta(AgentStudentSerializer.Meta):
        fields = AgentStudentSerializer.Meta.fields + [
            'status_timeline', 'commission_record', 'documents'
        ]

    def get_status_timeline(self, obj):
        from verification.models import AuditLog
        if not obj.application:
            return []
        
        logs = AuditLog.objects.filter(
            application=obj.application
        ).order_by('timestamp')
        
        timeline = []
        for log in logs:
            if 'status' in (log.after_json or {}):
                timeline.append({
                    'status': log.after_json['status'],
                    'timestamp': log.timestamp,
                    'action': log.action
                })
        return timeline

    def get_commission_record(self, obj):
        commission = CommissionRecord.objects.filter(student=obj).first()
        if not commission:
            return None
        return CommissionRecordSerializer(commission).data

    def get_documents(self, obj):
        from documents.models import Document
        docs = Document.objects.filter(student=obj.user)
        return [{
            'type': d.document_type,
            'status': d.status,
            'confidence': d.ocr_result.confidence if hasattr(d, 'ocr_result') and d.ocr_result else None,
            'updated_at': d.updated_at
        } for d in docs]
