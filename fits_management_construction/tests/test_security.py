from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install", "fits_mk")
class TestPublicRoutesClosed(HttpCase):
    """Routes that used to be auth='public' now require a logged-in user."""

    def test_stakeholder_excel_requires_login(self):
        res = self.url_open("/download/stakeholder_analysis_excel/1", allow_redirects=False)
        self.assertIn(res.status_code, (302, 303))
        self.assertIn("/web/login", res.headers.get("Location", ""))

    def test_risk_mitigation_api_requires_login(self):
        res = self.url_open(
            "/api/analysis_risk_mitigation",
            data='{"jsonrpc": "2.0", "method": "call", "params": {}}',
            headers={"Content-Type": "application/json"},
        )
        self.assertIn("SessionExpiredException", res.text)
        self.assertFalse(self.env["analysis.risk.mitigation"].search_count([("name", "=", "anon")]))

    def test_no_hardcoded_api_keys(self):
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        offenders = [
            str(p.relative_to(root)) for p in root.rglob("*.py")
            if "sk-proj-" in p.read_text(encoding="utf-8") and p.name != "test_security.py"
        ]
        self.assertFalse(offenders, f"hard-coded API keys in {offenders}")
