"""Read-only sync of projects and analytic accounts from the Fujicon Odoo 12 server (decision K4).

The Odoo 12 server is only ever *read*: every remote call goes through ``_v12_call`` which
allows read methods only.  Nothing is written back.  Credentials live in system parameters
(Settings), never in code.
"""
import ast
import logging
import xmlrpc.client

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PARAM = "fits_management_construction.v12_"
READ_METHODS = frozenset({"search_read", "read", "search", "search_count", "fields_get"})
DEFAULT_DOMAIN = "[('project_category', '=', 'project')]"


class ProjectProject(models.Model):
    _inherit = "project.project"

    mk_source_project_id = fields.Integer(
        "Odoo 12 Project ID", index=True, copy=False, readonly=True,
        help="Project id on the Fujicon Odoo 12 server this project is synced from.")
    mk_source_code = fields.Char("Project Code", index=True, copy=False,
                                 help="Analytic account code on Odoo 12, e.g. IT-AGRO.")
    mk_synced_at = fields.Datetime("Last Synced", readonly=True, copy=False)

    _mk_source_project_unique = models.Constraint(
        "UNIQUE(mk_source_project_id)", "This Odoo 12 project is already linked to another project.")


class MkV12Sync(models.AbstractModel):
    _name = "fits.mk.v12.sync"
    _description = "Read-only sync from Fujicon Odoo 12"

    # ---------------------------------------------------------------- connection
    @api.model
    def _v12_config(self):
        ICP = self.env["ir.config_parameter"].sudo()
        cfg = {k: ICP.get_param(PARAM + k) or "" for k in ("url", "db", "login", "password", "domain")}
        missing = [k for k in ("url", "db", "login", "password") if not cfg[k]]
        if missing:
            raise UserError(_("Odoo 12 sync is not configured (missing: %s).", ", ".join(missing)))
        cfg["url"] = cfg["url"].rstrip("/")
        return cfg

    @api.model
    def _v12_call(self, cfg, model, method, args, kwargs=None):
        if method not in READ_METHODS:
            raise UserError(_("Odoo 12 sync is read-only: method %s is not allowed.", method))
        if "uid" not in cfg:
            common = xmlrpc.client.ServerProxy(f"{cfg['url']}/xmlrpc/2/common", allow_none=True)
            cfg["uid"] = common.authenticate(cfg["db"], cfg["login"], cfg["password"], {})
            if not cfg["uid"]:
                raise UserError(_("Odoo 12 login failed."))
        obj = xmlrpc.client.ServerProxy(f"{cfg['url']}/xmlrpc/2/object", allow_none=True)
        return obj.execute_kw(cfg["db"], cfg["uid"], cfg["password"], model, method, args, kwargs or {})

    # ---------------------------------------------------------------- sync
    @api.model
    def _source_domain(self, cfg):
        try:
            domain = ast.literal_eval(cfg.get("domain") or DEFAULT_DOMAIN)
        except (ValueError, SyntaxError) as exc:
            raise UserError(_("Invalid Odoo 12 project filter: %s", exc)) from exc
        if not isinstance(domain, list):
            raise UserError(_("Invalid Odoo 12 project filter: it must be a list."))
        return domain

    @api.model
    def sync_projects(self):
        """Create or update projects (and their analytic accounts) from Odoo 12. Returns stats."""
        cfg = self._v12_config()
        remote = self._v12_call(cfg, "project.project", "search_read", [self._source_domain(cfg)], {
            "fields": ["name", "partner_id", "date_start", "date", "analytic_account_id", "active"],
            "context": {"active_test": False},
        })
        analytic_ids = sorted({p["analytic_account_id"][0] for p in remote if p.get("analytic_account_id")})
        codes = {}
        if analytic_ids:
            for acc in self._v12_call(cfg, "account.analytic.account", "read", [analytic_ids], {"fields": ["code"]}):
                codes[acc["id"]] = acc.get("code") or ""
        return self._apply_remote_projects(remote, codes)

    @api.model
    def _apply_remote_projects(self, remote, codes):
        Project = self.env["project.project"].with_context(active_test=False)
        stats = {"created": 0, "updated": 0, "unchanged": 0}
        now = fields.Datetime.now()
        for rec in remote:
            analytic = rec.get("analytic_account_id") or False
            code = codes.get(analytic[0], "") if analytic else ""
            vals = {
                "name": rec["name"],
                "mk_source_code": code or False,
                "date_start": rec.get("date_start") or False,
                "date": rec.get("date") or False,
                "active": rec.get("active", True),
            }
            partner = self._match_partner(rec.get("partner_id"))
            if partner:
                vals["partner_id"] = partner.id
            project = Project.search([("mk_source_project_id", "=", rec["id"])], limit=1)
            if not project:
                vals["mk_source_project_id"] = rec["id"]
                vals["mk_synced_at"] = now
                project = Project.create(vals)
                stats["created"] += 1
            else:
                changes = {k: v for k, v in vals.items() if self._differs(project, k, v)}
                if changes:
                    project.write({**changes, "mk_synced_at": now})
                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
            self._ensure_analytic(project, code)
        _logger.info("Odoo 12 project sync: %s", stats)
        return stats

    @api.model
    def _differs(self, record, fname, value):
        current = record[fname]
        if record._fields[fname].type == "many2one":
            current = current.id
        elif record._fields[fname].type == "date":
            current = fields.Date.to_string(current) if current else False
        return (current or False) != (value or False)

    @api.model
    def _match_partner(self, remote_partner):
        """Partners are matched by exact name; unknown partners are created (no write to Odoo 12)."""
        if not remote_partner:
            return self.env["res.partner"]
        name = remote_partner[1]
        Partner = self.env["res.partner"]
        return Partner.search([("name", "=", name)], limit=1) or Partner.create({"name": name, "is_company": True})

    @api.model
    def _ensure_analytic(self, project, code):
        """Give the project an analytic account named after it, carrying the Odoo 12 code."""
        if "account_id" not in project._fields or project.account_id:
            if project.account_id and code and project.account_id.code != code:
                project.account_id.code = code
            return
        plan = self.env["account.analytic.plan"].search([], limit=1) or \
            self.env["account.analytic.plan"].create({"name": "Projects"})
        project.account_id = self.env["account.analytic.account"].create({
            "name": project.name, "code": code or False, "plan_id": plan.id,
            "company_id": project.company_id.id or False,
        })

    @api.model
    def _cron_sync_projects(self):
        try:
            self.sync_projects()
        except UserError as exc:
            _logger.warning("Odoo 12 project sync skipped: %s", exc)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mk_v12_url = fields.Char("Odoo 12 URL", config_parameter=PARAM + "url")
    mk_v12_db = fields.Char("Odoo 12 Database", config_parameter=PARAM + "db")
    mk_v12_login = fields.Char("Odoo 12 Login", config_parameter=PARAM + "login")
    mk_v12_password = fields.Char("Odoo 12 Password / API Key", config_parameter=PARAM + "password")
    mk_v12_domain = fields.Char("Odoo 12 Project Filter", config_parameter=PARAM + "domain",
                                default=DEFAULT_DOMAIN)

    def action_mk_v12_sync_now(self):
        self.ensure_one()
        self.execute()
        stats = self.env["fits.mk.v12.sync"].sync_projects()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Odoo 12 sync done"),
                "message": _("%(created)s created, %(updated)s updated, %(unchanged)s unchanged", **stats),
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
