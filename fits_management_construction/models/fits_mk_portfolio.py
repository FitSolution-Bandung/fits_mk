from odoo import api, fields, models

# models that carry MK field documents, with their project field (see _mk_project_field)
MK_DOCUMENT_MODELS = [
    "daily.report", "document.report", "nonconformance.report.form", "material.approval",
    "working.drawing", "field.change", "work.request", "work.correction", "defect.list",
    "feasibility.inspection.document", "final.submission", "foundry.permits",
    "execution.permits", "implementation.permits", "overtime.form", "supervision.form",
    "weather.monitoring", "goods.submission", "document.inbond.outbond",
    "health.safety.environment", "analysis.risk.mitigation", "stakeholder.analysis",
]


class ProjectProject(models.Model):
    _inherit = "project.project"

    mk_daily_report_count = fields.Integer("Daily Reports", compute="_compute_mk_counts")
    mk_ncr_open_count = fields.Integer("Open NCR", compute="_compute_mk_counts")
    mk_document_count = fields.Integer("MK Documents", compute="_compute_mk_counts")
    mk_plan_weight = fields.Float("Plan (%)", compute="_compute_mk_progress", digits=(16, 2))
    mk_actual_weight = fields.Float("Actual (%)", compute="_compute_mk_progress", digits=(16, 2))
    mk_deviation = fields.Float("Deviation (%)", compute="_compute_mk_progress", digits=(16, 2))
    mk_progress_state = fields.Selection([
        ("none", "No S-Curve"),
        ("on_track", "On Track"),
        ("late", "Late"),
        ("critical", "Critical"),
    ], string="Progress Status", compute="_compute_mk_progress")

    def _mk_count(self, model_name, extra_domain=()):
        Model = self.env[model_name]
        field = type(Model)._mk_project_field
        groups = Model._read_group([(field, "in", self.ids), *extra_domain], [field], ["__count"])
        return {project.id: count for project, count in groups}

    def _compute_mk_counts(self):
        daily = self._mk_count("daily.report")
        ncr = self._mk_count("nonconformance.report.form", [("status", "=", "draft")])
        totals = {}
        for name in MK_DOCUMENT_MODELS:
            if name not in self.env:
                continue
            for pid, count in self._mk_count(name).items():
                totals[pid] = totals.get(pid, 0) + count
        for project in self:
            project.mk_daily_report_count = daily.get(project.id, 0)
            project.mk_ncr_open_count = ncr.get(project.id, 0)
            project.mk_document_count = totals.get(project.id, 0)

    @api.model
    def _mk_deviation_thresholds(self):
        ICP = self.env["ir.config_parameter"].sudo()
        late = float(ICP.get_param("fits_management_construction.deviation_late", 5.0))
        critical = float(ICP.get_param("fits_management_construction.deviation_critical", 10.0))
        return late, critical

    def _compute_mk_progress(self):
        late, critical = self._mk_deviation_thresholds()
        curves = self.env["project.curve.s"].search(
            [("project_id", "in", self.ids)], order="write_date desc, id desc")
        latest = {}
        for curve in curves:
            latest.setdefault(curve.project_id.id, curve)
        for project in self:
            curve = latest.get(project.id)
            if not curve:
                project.mk_plan_weight = project.mk_actual_weight = project.mk_deviation = 0.0
                project.mk_progress_state = "none"
                continue
            project.mk_plan_weight = curve.plan_weight
            project.mk_actual_weight = curve.actual_weight
            project.mk_deviation = curve.deviasi
            if curve.deviasi <= -critical:
                project.mk_progress_state = "critical"
            elif curve.deviasi <= -late:
                project.mk_progress_state = "late"
            else:
                project.mk_progress_state = "on_track"

    def _mk_action(self, model_name, name, extra_domain=()):
        self.ensure_one()
        field = type(self.env[model_name])._mk_project_field
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model_name,
            "view_mode": "list,form",
            "domain": [(field, "=", self.id), *extra_domain],
            "context": {f"default_{field}": self.id},
        }

    def action_view_mk_daily_reports(self):
        return self._mk_action("daily.report", "Daily Reports")

    def action_view_mk_ncr(self):
        return self._mk_action("nonconformance.report.form", "Non-Conformance Reports")
