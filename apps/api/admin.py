from django.contrib import admin

from apps.api.models import AnalysisSession


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "mode", "status", "decision", "project_label", "created_at")
    list_filter = ("mode", "status", "input_type")
    search_fields = ("room_id", "audit_id", "project_label")
    readonly_fields = ("created_at", "updated_at", "result_json")
