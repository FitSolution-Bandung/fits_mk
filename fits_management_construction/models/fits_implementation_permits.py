from babel.dates import format_date
from datetime import datetime
from odoo import models, fields, api, exceptions

# Model Execution Permits / Daftar izin Pelaksanaan
class ImplementationPermits(models.Model):
    _name = 'implementation.permits'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Implementation Permits'
    _rec_name = 'no_doc'

    implementation_permits_ids = fields.One2many('implementation.permits.detail', 'implementation_permits_id', string="Implementation Permits")
    name_contractor = fields.Many2one('res.partner', string="Contractor")
    name_consultant = fields.Many2one('res.partner', string="Consultant")
    no_doc = fields.Char(string="No Form", readonly=True, required=True, copy=False, default='New')
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

    @api.model
    def create(self, vals):
        if vals.get('no_doc', 'New') == 'New':
            vals['no_doc'] = self.env['ir.sequence'].next_by_code('no.doc') or 'New'
        result = super(ImplementationPermits, self).create(vals)
        return result
    
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
        return super(ImplementationPermits, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")
    
class ImplementationPermitsDetail(models.Model):
    _name = 'implementation.permits.detail'
    _description = 'Implementation Permits Detail'
    _rec_name = 'name_items'

    implementation_permits_id = fields.Many2one('implementation.permits', string="Implementation")
    name_items                = fields.Char(string="Work Items")
    date                      = fields.Date(string="Date")
    implementation_method     = fields.Char(string="Implementation Method")
    volume                    = fields.Char(string="Volume")
    tools                     = fields.Char(string="Tools")
    manpower                  = fields.Char(string="Man Power")
    description               = fields.Char(string="Desc")
