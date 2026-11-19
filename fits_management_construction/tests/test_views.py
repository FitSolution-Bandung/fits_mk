from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install", "fits_mk")
class TestActionsAndViews(TransactionCase):
    """Every window action of the module opens: its views compile and its model can be read."""

    def test_actions_open(self):
        data = self.env["ir.model.data"].search([
            ("module", "=", "fits_management_construction"),
            ("model", "=", "ir.actions.act_window"),
        ])
        self.assertTrue(data, "module defines no window actions")
        problems = []
        for xmlid in data:
            action = self.env["ir.actions.act_window"].browse(xmlid.res_id)
            modes = [m for m in (action.view_mode or "").split(",") if m]
            try:
                model = self.env[action.res_model]
                model.get_views([(False, m) for m in modes] + [(False, "search")])
                domain = safe_eval(action.domain or "[]", {"uid": self.env.uid, "context": {}})
                model.search_read(domain, limit=1)
            except Exception as exc:  # noqa: BLE001 - collect every broken action
                problems.append(f"{xmlid.name} ({action.res_model}): {exc}")
        self.assertFalse(problems, "Broken actions:\n" + "\n".join(problems))

    def test_kanban_views_use_card_template(self):
        """Odoo 19 kanban renders only the 'card' template; 'kanban-box' breaks in the browser."""
        views = self.env["ir.ui.view"].search([("type", "=", "kanban")]).filtered(
            lambda v: v.xml_id.startswith("fits_management_construction."))
        old = [v.xml_id for v in views if 't-name="kanban-box"' in v.arch_db]
        self.assertFalse(old, f"kanban views still using kanban-box: {old}")

    def test_reports_reference_existing_templates(self):
        reports = self.env["ir.actions.report"].search([("model", "!=", False)]).filtered(
            lambda r: r.report_name.startswith("fits_management_construction."))
        self.assertTrue(reports)
        for report in reports:
            self.assertTrue(
                self.env["ir.ui.view"]._get_template_view(report.report_name),
                f"missing QWeb template for {report.report_name}")
