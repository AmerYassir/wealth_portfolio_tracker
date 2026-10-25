"""Audit trail for agent tool calls.

One row per server-side tool invocation, whether it succeeded or failed.
The `user` FK is nullable because a tool can fire before `get_user` resolves
(in which case the logger records what it has and moves on).
"""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    tool_name = models.CharField(max_length=128, db_index=True)
    arguments = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, db_index=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["tool_name", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        who = self.user.username if self.user else "anonymous"
        return f"{self.tool_name} by {who} ({self.status})"
