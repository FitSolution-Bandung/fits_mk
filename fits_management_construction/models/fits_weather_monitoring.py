from odoo import models, fields, exceptions, api
from babel.dates import format_date
from calendar import monthrange
from datetime import datetime

# Model Defect List / Daftar Cacat
class WeatherMonitoringForm(models.Model):
    _name = 'weather.monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Weather Monitoring'
    _rec_name = 'name_project'

    name_project          = fields.Many2one('project.project', string="Name Project", required=True)
    location              = fields.Char(string="Location")
    date                  = fields.Date(string="Weather Date", required=True)
    month_years           = fields.Char(string="Month & Years", compute="_compute_month_years")
    days_in_month         = fields.Integer(string="Days in Month", compute="_compute_days_in_month")
    active = fields.Boolean(string="Active", default=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    @api.depends('date')
    def _compute_days_in_month(self):
        for record in self:
            if record.date:
                # Mengambil bulan dan tahun dari date
                date_obj = datetime.strptime(str(record.date), '%Y-%m-%d')
                _, days_in_month = monthrange(date_obj.year, date_obj.month)
                record.days_in_month = days_in_month
            else:
                record.days_in_month = 0
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(WeatherMonitoringForm, self).write(vals)

    @api.depends('date')
    def _compute_month_years(self):
        for record in self:
            if record.date:
                # Mengambil nama bulan dalam bahasa Indonesia
                record.month_years = format_date(record.date, 'MMMM - yyyy', locale='id_ID')
            else:
                record.month_years = ''

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")