from odoo import models
from odoo.fields import Domain


class IrRule(models.Model):
    """MK documents follow the access of their project (decision K11).

    A model opts in by declaring ``_mk_project_field = '<many2one to project.project>'``.
    For such models, the record rules of ``project.project`` (privacy/visibility,
    followers, members, companies) are added on top of the model's own rules, the
    same way Odoo combines rules of ``_inherits`` parents.  A user who cannot read a
    project cannot read, change or delete the MK documents of that project.
    """

    _inherit = "ir.rule"

    def _compute_domain(self, model_name, mode="read"):
        domain = super()._compute_domain(model_name, mode)
        field_name = getattr(self.env.registry.get(model_name), "_mk_project_field", None)
        if not field_name or self.env.su:
            return domain
        project_domain = super()._compute_domain("project.project", "read")
        if project_domain.is_true():
            return domain
        model = self.env[model_name]
        return (domain & Domain(field_name, "any", project_domain)).optimize(model)
