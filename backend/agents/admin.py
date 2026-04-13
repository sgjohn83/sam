from django.contrib import admin
from .models import AgentProfile, CommissionRecord

@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('agency_name', 'user', 'commission_rate', 'is_verified', 'is_active')
    list_filter = ('is_verified', 'is_active')
    search_fields = ('agency_name', 'user__email', 'user__full_name')
    readonly_fields = ('total_students_referred', 'total_commission_earned', 'verified_at', 'created_at', 'updated_at')

@admin.register(CommissionRecord)
class CommissionRecordAdmin(admin.ModelAdmin):
    list_display = ('agent', 'student', 'commission_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('agent__agency_name', 'student__user__full_name', 'application__application_number')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'paid_at')
