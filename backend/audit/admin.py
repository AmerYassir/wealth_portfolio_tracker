from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "tool_name", "user", "status", "short_error")
    list_filter = ("status", "tool_name")
    search_fields = ("tool_name", "user__username", "error_message")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "user", "tool_name", "arguments", "status", "error_message")

    @admin.display(description="Error")
    def short_error(self, obj):
        return (obj.error_message[:60] + "…") if len(obj.error_message) > 60 else obj.error_message

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
