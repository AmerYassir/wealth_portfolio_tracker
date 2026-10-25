"""Proves the DatabaseAuditLogger writes to AuditLog and never raises."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from agent.agent_tools import set_current_user
from audit.logger import DatabaseAuditLogger
from audit.models import AuditLog


class DatabaseAuditLoggerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("audit_user", password="x")

    def test_success_writes_row(self):
        set_current_user(self.user)
        logger = DatabaseAuditLogger()
        logger.record("list_my_portfolios", {"portfolio_id": 1}, success=True)
        row = AuditLog.objects.get()
        self.assertEqual(row.tool_name, "list_my_portfolios")
        self.assertEqual(row.user, self.user)
        self.assertEqual(row.status, AuditLog.Status.SUCCESS)
        self.assertEqual(row.arguments, {"portfolio_id": 1})
        self.assertEqual(row.error_message, "")

    def test_failure_writes_row_with_error(self):
        set_current_user(self.user)
        logger = DatabaseAuditLogger()
        logger.record("get_portfolio_summary", {"portfolio_id": 2}, success=False, error="not found or access denied")
        row = AuditLog.objects.get()
        self.assertEqual(row.status, AuditLog.Status.FAILURE)
        self.assertEqual(row.error_message, "not found or access denied")

    def test_anonymous_user_is_null(self):
        from django.contrib.auth.models import AnonymousUser
        set_current_user(AnonymousUser())
        logger = DatabaseAuditLogger()
        logger.record("list_my_portfolios", {}, success=True)
        row = AuditLog.objects.get()
        self.assertIsNone(row.user)

    def test_logger_never_raises_on_db_error(self):
        """If AuditLog.objects.create fails, record() must swallow it."""
        from unittest.mock import patch
        set_current_user(self.user)
        logger = DatabaseAuditLogger()
        with patch("audit.logger.AuditLog.objects.create", side_effect=RuntimeError("boom")):
            # Should not raise
            logger.record("list_my_portfolios", {}, success=True)
        self.assertEqual(AuditLog.objects.count(), 0)
