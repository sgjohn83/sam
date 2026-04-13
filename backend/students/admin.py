from django.contrib import admin
from .models import StudentProfile, PushToken

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'domicile_state')
    list_filter = ('category', 'gender')
    search_fields = ('user__email', 'user__full_name')


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "created_at")
    list_filter = ("platform", "created_at")
    search_fields = ("user__email", "user__full_name", "token")
