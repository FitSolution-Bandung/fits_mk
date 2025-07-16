from odoo import models, fields, api

class DocumentReport(models.Model):
    _name = 'document.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Document Report'
    _rec_name = 'no_doc'

    no_doc = fields.Char(string="No Document Report", readonly=True, required=True, copy=False, default='New')
    date = fields.Date(string="Date")
    project = fields.Many2one('project.project', string='Project', required=True)
    daily_report = fields.Many2one('daily.report', string='No Daily Report')
    documentation_ids = fields.One2many('documentation', 'doc_report_id', string="Documentation")
    active = fields.Boolean(string="Active", default=True)

    @api.onchange('daily_report')
    def _onchange_daily_report(self):
        if self.daily_report:
            self.date = self.daily_report.date
            self.project = self.daily_report.project
        else:
            self.date = False
            self.project = False

    def action_view_daily_report(self):
        self.ensure_one()
        return {
            'name': 'Daily Report',
            'domain': [('id', '=', self.daily_report.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'daily.report',
            'type': 'ir.actions.act_window',
            'context': {'default_id': self.daily_report.id},
        }

    @api.model
    def create(self, vals):
        if vals.get('no_doc', 'New') == 'New':
            vals['no_doc'] = self.env['ir.sequence'].next_by_code('no.doc') or 'New'
        result = super(DocumentReport, self).create(vals)
        return result

class Documentation(models.Model):
    _name = 'documentation'
    _description = 'Documentation'

    doc_report_id = fields.Many2one('document.report', string="Document Report")
    img = fields.Image(string='Image')
    desc = fields.Char('Description')