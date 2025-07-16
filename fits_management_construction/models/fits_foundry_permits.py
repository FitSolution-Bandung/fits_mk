from babel.dates import format_date
from datetime import datetime
from odoo import models, fields, api, exceptions

# Model Defect List / Daftar Cacat
class FoundryPermits(models.Model):
    _name = 'foundry.permits'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Foundry Permits'
    _rec_name = 'name_project'

    name_project    = fields.Many2one('project.project', string="Name Project", required=True)
    package         = fields.Char(string="Work Package")
    no_permits      = fields.Char(string="No Permits", readonly=True, required=True, copy=False, default='New')
    date            = fields.Date(string="Date")
    name_contractor = fields.Many2one('res.partner', string="Name Contractor")
    name_consultant = fields.Many2one('res.partner', string="Name Consultant")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    province        = fields.Many2one('res.country.state', string="Province", domain="[('country_id', '=', 'Indonesia')]")
    city            = fields.Many2one('location', string="City", domain="[('province', '=', province)]")
    month_name      = fields.Char(string="Month Name", compute="_compute_month_name")
    active = fields.Boolean(string="Active", default=True)

    work_detail_ids = fields.One2many('foundry.work.detail', 'foundry_permits_id', string="Work Details")
    approval_notes_ids = fields.One2many('approval.notes', 'foundry_permits_id', string="Approval Notes")

    @api.model
    def create(self, vals):
        if vals.get('no_permits', 'New') == 'New':
            vals['no_permits'] = self.env['ir.sequence'].next_by_code('no.permits') or 'New'
        result = super(FoundryPermits, self).create(vals)
        return result

    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(FoundryPermits, self).write(vals)

    @api.depends('date')
    def _compute_month_name(self):
        for record in self:
            if record.date:
                # Mengambil nama bulan dalam bahasa Indonesia
                record.month_name = format_date(datetime.strptime(str(record.date), '%Y-%m-%d'), 'MMMM', locale='id_ID')
            else:
                record.month_name = ''

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")
    
class FoundryWorkDetail(models.Model):
    _name = 'foundry.work.detail'
    _description = 'Foundry Work Detail'
    _rec_name = 'name_items'

    foundry_permits_id  = fields.Many2one('foundry.permits', string="Foundry Permits")
    name_items          = fields.Char(string="Work Items")
    volume              = fields.Float(string="Volume")
    concrete_class      = fields.Char(string="Concrete Class")
    description         = fields.Char(string="Description")

class ApprovalNotes(models.Model):
    _name = 'approval.notes'
    _description = 'Approval Notes'
    _rec_name = 'work_types'

    foundry_permits_id  = fields.Many2one('foundry.permits', string="Foundry Permits")
    work_types          = fields.Char(string="Work Types")
    approval_notes      = fields.Char(string="Approval Notes")
