"""Regression tests for amunet.quality.audit.log immutability.

ISO 13485 cl. 4.2.5 and 21 CFR Part 11 demand that audit trail records
be immutable: once written, they cannot be modified or deleted by normal
operations. The amunet.quality.audit.log model overrides `write` and
`unlink` to raise AccessDenied unless invoked via `.sudo()` (legitimate
admin maintenance) or with the `install_mode` context (module
install/migrate).

These tests freeze that invariant so any future refactor that removes the
protection will fail the test suite loudly.
"""

from odoo.exceptions import AccessDenied
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "amunet_audit_log")
class TestAuditLogImmutability(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AuditLog = cls.env["amunet.quality.audit.log"]

    def _make_log(self):
        return self.AuditLog.create(
            {
                "model_name": "res.partner",
                "res_id": 1,
                "field_name": "name",
                "old_value": "original",
                "new_value": "changed",
            }
        )

    def test_write_is_blocked_for_normal_user(self):
        """Direct write() must raise AccessDenied."""
        log = self._make_log()
        with self.assertRaises(AccessDenied):
            log.write({"new_value": "tampered"})
        # Value did not change
        self.assertEqual(log.new_value, "changed")

    def test_unlink_is_blocked_for_normal_user(self):
        """Direct unlink() must raise AccessDenied."""
        log = self._make_log()
        with self.assertRaises(AccessDenied):
            log.unlink()
        # Record still exists
        self.assertTrue(log.exists())

    def test_sudo_write_is_allowed(self):
        """Explicit sudo() context allows write (for legitimate maintenance)."""
        log = self._make_log()
        log.sudo().write({"new_value": "admin-override"})
        self.assertEqual(log.new_value, "admin-override")

    def test_sudo_unlink_is_allowed(self):
        """Explicit sudo() context allows unlink (for legitimate maintenance)."""
        log = self._make_log()
        log_id = log.id
        log.sudo().unlink()
        self.assertFalse(self.AuditLog.browse(log_id).exists())

    def test_install_mode_context_write_is_allowed(self):
        """Module install/migrate context allows write (for upgrades)."""
        log = self._make_log()
        log.with_context(install_mode=True).write({"new_value": "migration"})
        self.assertEqual(log.new_value, "migration")
