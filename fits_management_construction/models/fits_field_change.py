from odoo import models, fields, api, exceptions

# Model Defect List / Daftar Cacat
class FieldChange(models.Model):
    _name = 'field.change'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Field Change'
    _rec_name = 'no_fcn'

    no_fcn = fields.Char(string="FCN", required=True)
    submission_date = fields.Date('Submission Date')

    no_contract = fields.Char(string="No Contract", readonly=True, required=True, copy=False, default='New')
    contract_date = fields.Date(string="Date")
    name_project = fields.Many2one('project.project', string="Name Project", required=True)
    name_package = fields.Char(string="Name Package")
    construction_service_provider = fields.Many2one('res.partner', string="Construction Service Provider")
    work_activity = fields.Char(string="Work Activity")
    active = fields.Boolean(string="Active", default=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    location            = fields.Char(string="Location")
    cost_center         = fields.Char(string="Cost Center")
    description         = fields.Text(string="Description")

    actual_condition = fields.Text(string="Actual Conditions")
    plan_change = fields.Text(string="Plan Changes")
    reason_change = fields.Text(string="Reason Changes")
    plan_change_date = fields.Date(string="Plan Change Date")
    
    @api.model
    def create(self, vals):
        if vals.get('no_contract', 'New') == 'New':
            vals['no_contract'] = self.env['ir.sequence'].next_by_code('no.contract') or 'New'
        result = super(FieldChange, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(FieldChange, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")