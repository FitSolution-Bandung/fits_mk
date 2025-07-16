from babel.dates import format_date
from datetime import datetime
from odoo import models, fields, api, exceptions

# Model Defect List / Daftar Cacat
class DefectList(models.Model):
    _name = 'defect.list'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Defect List'
    _rec_name = 'name_project'

    name_project    = fields.Many2one('project.project', string="Name Project", required=True)
    package         = fields.Char(string="Work Package")
    inspection_date = fields.Date(string="Inspection Date")
    defect_list_ids = fields.One2many('defect.list.detail', 'defect_list_id', string="Defect List")
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

    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(DefectList, self).write(vals)

    @api.depends('inspection_date')
    def _compute_month_name(self):
        for record in self:
            if record.inspection_date:
                # Mengambil nama bulan dalam bahasa Indonesia
                record.month_name = format_date(datetime.strptime(str(record.inspection_date), '%Y-%m-%d'), 'MMMM', locale='id_ID')
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
    
class DefectListDetail(models.Model):
    _name = 'defect.list.detail'
    _description = 'Defect List Detail'
    _rec_name = 'name_items'

    defect_list_id  = fields.Many2one('defect.list', string="Defect List")
    name_items      = fields.Char(string="Work Items")
    no_room         = fields.Char(string="No Rooms")
    condition       = fields.Char(string="Conditions")
    img_condition   = fields.Binary(string="Documentation", attachment=True)
