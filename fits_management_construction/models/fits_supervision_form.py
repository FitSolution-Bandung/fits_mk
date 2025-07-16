from babel.dates import format_date
from datetime import datetime
from odoo import models, fields, api, exceptions

# Model Defect List / Daftar Cacat
class SupervisionForm(models.Model):
    _name = 'supervision.form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Supervision Form'
    _rec_name = 'no_doc'

    no_doc                = fields.Char(string="No Doc", readonly=True, required=True, copy=False, default='New')
    date                  = fields.Date(string="Date")
    month_name            = fields.Char(string="Month Name", compute="_compute_month_name")
    # day_name              = fields.Char(string="Day", compute="_compute_day_name", store=True, readonly=True)
    province              = fields.Many2one('res.country.state', string="Province", domain="[('country_id', '=', 'Indonesia')]")
    city                  = fields.Many2one('location', string="City", domain="[('province', '=', province)]")
    active                = fields.Boolean(string="Active", default=True)
    contractor_name       = fields.Many2one('res.partner', string="Contractor Name")
    consultant_name       = fields.Many2one('res.partner', string="Contractor Name")
    status                = fields.Selection([
                                ('draft', 'Draft'),
                                ('confirm', 'Confirmed'),
                                ('cancelled', 'Cancelled')
                            ], string='Status', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('no_doc', 'New') == 'New':
            vals['no_doc'] = self.env['ir.sequence'].next_by_code('no.doc') or 'New'
        result = super(SupervisionForm, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(SupervisionForm, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")

    # @api.depends('date')
    # def _compute_day_name(self):
    #     day_mapping = {
    #         0: 'Senin',
    #         1: 'Selasa',
    #         2: 'Rabu',
    #         3: 'Kamis',
    #         4: 'Jumat',
    #         5: 'Sabtu',
    #         6: 'Minggu',
    #     }

    #     for record in self:
    #         if record.date:
    #             # Mendapatkan angka hari (0 = Senin, 6 = Minggu)
    #             day_number = record.date.weekday()
    #             # Mapping ke nama hari
    #             record.day_name = day_mapping.get(day_number, '')
    #         else:
    #             record.day_name = ''

    @api.depends('date')
    def _compute_month_name(self):
        for record in self:
            if record.date:
                # Mengambil nama bulan dalam bahasa Indonesia
                record.month_name = format_date(datetime.strptime(str(record.date), '%Y-%m-%d'), 'MMMM', locale='id_ID')
            else:
                record.month_name = ''