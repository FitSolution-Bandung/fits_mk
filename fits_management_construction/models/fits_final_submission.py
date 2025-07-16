from odoo import models, fields, api, exceptions

# Model Execution Permits / Daftar izin Pelaksanaan
class FinalSubmissionForm(models.Model):
    _name = 'final.submission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Final Submission'
    _rec_name = 'no_doc'

    name_maintenance_service = fields.Many2one('res.partner', string="Contractor")
    name_consultant = fields.Many2one('res.partner', string="Consultant")
    name_responsible = fields.Many2one('res.partner', string="Responsible")
    no_doc = fields.Char(string="No Form", readonly=True, required=True, copy=False, default='New')
    submission_date = fields.Date(string="Submission Date", required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    no_contract = fields.Char(string="No Contract", required=True)
    contract_date = fields.Date(string="Contract Date", required=True)
    package_name = fields.Char(string="Package Name")

    project_name = fields.Many2one('project.project', string="Name Project", required=True)
    work_activity = fields.Char(string="Work Activity")
    location = fields.Char(string="Location")
    description = fields.Text(string="Description")
    construction_service_provider = fields.Char(string="Construction Provider")
    budget_by = fields.Char(string="Budget")

    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals):
        if vals.get('no_doc', 'New') == 'New':
            vals['no_doc'] = self.env['ir.sequence'].next_by_code('no.doc') or 'New'
        result = super(FinalSubmissionForm, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(FinalSubmissionForm, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")
