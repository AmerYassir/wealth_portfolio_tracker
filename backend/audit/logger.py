"""Database-backed AuditLogger.

Implements the `AuditLogger` Protocol that django-ag-ui expects. Every
server-side tool call routes through `record()`; we persist it and swallow
any logging-side error so a broken audit table never breaks the agent.

The ORM write runs in a dedicated OS thread because `record()` is called
from an async context (AGUIServer runs under ASGI). Django forbids sync ORM
calls from the event loop, and asgiref's async_to_sync refuses to run inside
a running loop. A plain daemon thread has no event loop, so the write is
legal; we don't wait for it because audit logging is not on the agent's
critical path.
"""
import logging
import threading

from django_ag_ui import AuditLogger

from agent.agent_tools import _current_user
from audit.models import AuditLog

logger = logging.getLogger(__name__)


class DatabaseAuditLogger(AuditLogger):
    def record(self, event, **kwargs):
        """
        `event` is a django-ag-ui AuditEvent object with:
            tool_name, arguments_repr, success, error, duration_ms,
            result_size, organization_id, target_type, target_id, ip_address

        The library calls this signature; earlier code that took
        (tool_name, arguments, success, error) was wrong for 0.64+.
        """
        try:
            user = _current_user.get()
            if user is not None and not getattr(user, "is_authenticated", False):
                user = None

            tool_name = getattr(event, "tool_name", None) or "unknown"
            success = bool(getattr(event, "success", True))
            error = getattr(event, "error", None) or ""

            # arguments_repr is a string in the AuditEvent; keep it as-is.
            args_repr = getattr(event, "arguments_repr", "") or ""
            arguments = {"_repr": args_repr} if args_repr else {}

            def _write():
                try:
                    AuditLog.objects.create(
                        user=user,
                        tool_name=tool_name,
                        arguments=arguments,
                        status=AuditLog.Status.SUCCESS if success else AuditLog.Status.FAILURE,
                        error_message=error,
                    )
                except Exception:
                    logger.exception("Failed to write AuditLog for tool %s", tool_name)

            threading.Thread(target=_write, daemon=True).start()
        except Exception:
            # Never let audit failure break a tool call.
            logger.exception("Audit logger setup failed for %r", event)