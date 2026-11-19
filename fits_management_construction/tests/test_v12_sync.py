from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

SYNC = "odoo.addons.fits_management_construction.models.fits_mk_v12_sync.MkV12Sync"

REMOTE_V1 = [
    {"id": 101, "name": "[IT-AGRO] Implementasi Odoo Agroqu", "partner_id": [7, "PT Agroqu"],
     "date_start": "2026-01-05", "date": "2026-06-30", "analytic_account_id": [55, "IT-AGRO"], "active": True},
    {"id": 102, "name": "[MK-GDG] Pengawasan Gedung", "partner_id": False,
     "date_start": False, "date": False, "analytic_account_id": False, "active": True},
]
CODES = [{"id": 55, "code": "IT-AGRO"}]


@tagged("post_install", "-at_install", "fits_mk")
class TestV12Sync(TransactionCase):
    """K4: projects come from Odoo 12, read-only. The remote server is mocked."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ICP = cls.env["ir.config_parameter"]
        for key, value in {"url": "https://v12.test", "db": "v12", "login": "bot", "password": "x"}.items():
            ICP.set_param(f"fits_management_construction.v12_{key}", value)
        cls.Sync = cls.env["fits.mk.v12.sync"]

    def _run(self, projects):
        def fake_call(_self, cfg, model, method, args, kwargs=None):
            if model == "project.project":
                return [dict(p) for p in projects]
            return CODES
        with patch(f"{SYNC}._v12_call", fake_call):
            return self.Sync.sync_projects()

    def _project(self, source_id):
        return self.env["project.project"].with_context(active_test=False).search(
            [("mk_source_project_id", "=", source_id)])

    def test_create_then_update_is_idempotent(self):
        self.assertEqual(self._run(REMOTE_V1), {"created": 2, "updated": 0, "unchanged": 0})
        agro = self._project(101)
        self.assertEqual(agro.name, "[IT-AGRO] Implementasi Odoo Agroqu")
        self.assertEqual(agro.mk_source_code, "IT-AGRO")
        self.assertEqual(agro.partner_id.name, "PT Agroqu")
        self.assertEqual(str(agro.date), "2026-06-30")
        self.assertEqual(agro.account_id.code, "IT-AGRO")

        self.assertEqual(self._run(REMOTE_V1), {"created": 0, "updated": 0, "unchanged": 2})

        changed = [dict(REMOTE_V1[0], date="2026-08-31"), dict(REMOTE_V1[1], active=False)]
        self.assertEqual(self._run(changed), {"created": 0, "updated": 2, "unchanged": 0})
        self.assertEqual(str(agro.date), "2026-08-31")
        self.assertFalse(self._project(102).active)
        self.assertEqual(self.env["project.project"].with_context(active_test=False).search_count(
            [("mk_source_project_id", "in", [101, 102])]), 2)

    def test_remote_calls_are_read_only(self):
        cfg = self.Sync._v12_config()
        for method in ("write", "create", "unlink", "action_done"):
            with self.assertRaises(UserError):
                self.Sync._v12_call(cfg, "project.project", method, [[1], {"name": "x"}])

    def test_requires_configuration(self):
        self.env["ir.config_parameter"].set_param("fits_management_construction.v12_url", "")
        with self.assertRaises(UserError):
            self.Sync.sync_projects()

    def test_cron_does_not_crash_when_unconfigured(self):
        self.env["ir.config_parameter"].set_param("fits_management_construction.v12_password", "")
        self.Sync._cron_sync_projects()
