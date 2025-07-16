from babel.dates import format_date
from datetime import datetime
from odoo import models, fields, api, exceptions

# Model Defect List / Daftar Cacat
class GoodsSubmissionForm(models.Model):
    _name = 'goods.submission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Goods Submission'
    _rec_name = 'no_meeting'

    name_project          = fields.Many2one('project.project', string="Name Project", required=True)
    work                  = fields.Char(string="Work")
    no_meeting            = fields.Char(string="No Meeting", readonly=True, required=True, copy=False, default='New')
    date                  = fields.Date(string="Date")
    month_name            = fields.Char(string="Month Name", compute="_compute_month_name")
    day_name              = fields.Char(string="Day", compute="_compute_day_name", store=True, readonly=True)
    location              = fields.Char(string="Location")
    active = fields.Boolean(string="Active", default=True)
    # total                 = fields.Float(string="Total", compute="_compute_total", store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    goods_submission_ids = fields.One2many('goods.submission.detail', 'goods_submission_id', string="Goods Submission Detail")
    
    # approved by
    approved_by           = fields.Many2one('hr.employee', string="Approved By")
    approved_by_job_title = fields.Char(related='approved_by.job_title', string="Approved By Job Title", readonly=True)
    approved_by_department = fields.Many2one(related='approved_by.department_id', string="Approved By Department", readonly=True)

    # checked by
    checked_by            = fields.Many2one('hr.employee', string="Checked By")
    checked_by_job_title  = fields.Char(related='checked_by.job_title', string="Checked By Job Title", readonly=True)
    checked_by_department = fields.Many2one(related='checked_by.department_id', string="Checked By Department", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('no_meeting', 'New') == 'New':
            vals['no_meeting'] = self.env['ir.sequence'].next_by_code('no.meeting') or 'New'
        result = super(GoodsSubmissionForm, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(GoodsSubmissionForm, self).write(vals)

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
    #     for record in self:
    #         if record.date:
    #             locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
    #             record.day_name = record.date.strftime('%A')
    #         else:
    #             record.day_name = ''


    @api.depends('date')
    def _compute_day_name(self):
        day_mapping = {
            0: 'Senin',
            1: 'Selasa',
            2: 'Rabu',
            3: 'Kamis',
            4: 'Jumat',
            5: 'Sabtu',
            6: 'Minggu',
        }

        for record in self:
            if record.date:
                # Mendapatkan angka hari (0 = Senin, 6 = Minggu)
                day_number = record.date.weekday()
                # Mapping ke nama hari
                record.day_name = day_mapping.get(day_number, '')
            else:
                record.day_name = ''

    @api.depends('date')
    def _compute_month_name(self):
        for record in self:
            if record.date:
                # Mengambil nama bulan dalam bahasa Indonesia
                record.month_name = format_date(datetime.strptime(str(record.date), '%Y-%m-%d'), 'MMMM', locale='id_ID')
            else:
                record.month_name = ''

    # @api.depends('goods_submission_ids.total_price')
    # def _compute_total(self):
    #     for record in self:
    #         total_sum = sum(line.total_price for line in record.goods_submission_ids)
    #         record.total = total_sum

class GoodsSubmissionDetail(models.Model):
    _name = 'goods.submission.detail'
    _description = 'Goods Submission Detail'
    _rec_name = 'tools'

    goods_submission_id  = fields.Many2one('goods.submission', string="Goods Submission")
    tools                = fields.Many2one('product.template', string="Tools", domain="[('rab_category', '!=', False)]")
    quantity             = fields.Char(string="Quantity")
    unit                 = fields.Many2one('uom.uom', string="Units")
    price                = fields.Float(string="Price")
    total_price          = fields.Float(string="Total Price", compute="_compute_total_price", store=True)
    notes                = fields.Char(string="Remarks")

    name = fields.Char(string="Description")
    display_type = fields.Selection([
        ('line_section', "Section"),
        ], default=False, string="Display Type")

    @api.depends('quantity', 'price')
    def _compute_total_price(self):
        for record in self:
            try:
                quantity = int(record.quantity) if record.quantity else 0
            except ValueError:
                quantity = 0
            record.total_price = quantity * record.price if quantity and record.price else 0