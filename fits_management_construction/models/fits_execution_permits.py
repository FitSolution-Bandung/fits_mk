from babel.dates import format_date
from datetime import datetime
from odoo import models, fields, api, exceptions

# Model Execution Permits / Daftar izin Pelaksanaan
class ExecutionPermits(models.Model):
    _name = 'execution.permits'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Execution Permits'
    _rec_name = 'attachment'

    attachment      = fields.Char(string="Attachment")
    execution_permits_ids = fields.One2many('execution.permits.detail', 'execution_permits_id', string="Execution Permits")
    name_client = fields.Many2one('res.partner', string="Name Client")
    name_consultant = fields.Many2one('res.partner', string="Name Consultant")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    province        = fields.Many2one('res.country.state', string="Province", domain="[('country_id', '=', 'Indonesia')]")
    city            = fields.Many2one('location', string="City", domain="[('province', '=', province)]")
    date            = fields.Date(string="Date")
    month_name      = fields.Char(string="Month Name", compute="_compute_month_name")
    active = fields.Boolean(string="Active", default=True)

    @api.depends('date')
    def _compute_month_name(self):
        for record in self:
            if record.date:
                # Mengambil nama bulan dalam bahasa Indonesia
                record.month_name = format_date(datetime.strptime(str(record.date), '%Y-%m-%d'), 'MMMM', locale='id_ID')
            else:
                record.month_name = ''
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(ExecutionPermits, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")
    
class ExecutionPermitsDetail(models.Model):
    _name = 'execution.permits.detail'
    _description = 'Execution Permits Detail'
    _rec_name = 'name_items'

    execution_permits_id = fields.Many2one('execution.permits', string="Defect List")
    name_items           = fields.Char(string="Work Items")
    permits_number       = fields.Char(string="Permits Number")
    submission_date      = fields.Date(string="Submission Date")
    approval_date        = fields.Date(string="Approval Date")
    description          = fields.Char(string="Description")
