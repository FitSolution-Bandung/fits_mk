from odoo import models, fields, api, exceptions

# Model Defect List / Daftar Cacat
class WorkingDrawing(models.Model):
    _name = 'working.drawing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Working Drawing'
    _rec_name = 'no_contract'

    no_form = fields.Char(string="No", required=True)
    submission_date = fields.Date('Submission Date')
    no_contract = fields.Char(string="No Contract", readonly=True, required=True, copy=False, default='New')
    contract_date = fields.Date(string="Date")
    work_activity = fields.Char(string="Work Activity")
    name_project = fields.Many2one('project.project', string="Name Project", required=True)
    name_package = fields.Char(string="Name Package")
    construction_service_provider = fields.Many2one('res.partner', string="Construction Service Provider")
    active = fields.Boolean(string="Active", default=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('no_contract', 'New') == 'New':
            vals['no_contract'] = self.env['ir.sequence'].next_by_code('no.contract') or 'New'
        result = super(WorkingDrawing, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(WorkingDrawing, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")