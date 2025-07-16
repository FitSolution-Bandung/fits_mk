from odoo import models, fields, api, exceptions
from datetime import datetime
from odoo.exceptions import ValidationError
from pdf2image import convert_from_bytes
from io import BytesIO
import base64, logging

_logger = logging.getLogger(__name__)
class DailyReport(models.Model):
    _name = 'daily.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Daily Report'
    _rec_name = 'no_dr'

    no_dr = fields.Char(string="No Daily Report", readonly=True, required=True, copy=False, default='New')
    date = fields.Date(string="Date")
    project = fields.Many2one('project.project', string='Project', required=True)
    wbs_ids = fields.One2many('wbs.dr', 'daily_report_id', string="WBS")
    mos_ids = fields.One2many('mos.dr', 'daily_report_id', string="MOS")
    weather_ids = fields.One2many('weather.dr', 'daily_report_id', string="Weather")    
    manpower_ids = fields.One2many('manpower.dr', 'daily_report_id', string="Manpower")
    equipment_ids = fields.One2many('equipment.dr', 'daily_report_id', string="Equipment")
    note_ids = fields.One2many('note.dr', 'daily_report_id', string="Note")
    monitoring_ids = fields.One2many('monitoring.dr', 'daily_report_id', string='Monitoring')
    active = fields.Boolean(string="Active", default=True)
    leader = fields.Many2one('hr.employee', string= "Team Leader", domain="[('id', 'in', name_mp_ids)]")
    supervisor = fields.Many2one('hr.employee', string= "Structure Supervisor", domain="[('id', 'in', name_mp_ids)]")
    name_mp_ids = fields.Many2many('hr.employee', compute='_get_name_mp', store=False)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('done', 'Done')
    ], string='Status', default='draft')
    progress_plan = fields.Float(string="Progress Rencana", compute='_get_plan_progress')
    progress_actual = fields.Float(string="Progress Aktual", compute='_get_actual_progress')
    deviasi = fields.Float(string="Deviasi", compute='_get_deviasi')
    
    @api.depends('project')
    def _get_plan_progress(self):
        for record in self:
            if record.project:
                start_date = record.project.date_start

                progres = self.env['task.progress'].search([
                    ('project', '=', record.project.id),
                    ('date', '>=', start_date),
                    ('date', '<=', record.date)
                ])

                bobot_plan = sum(progres.mapped('plan_weight'))

                record.progress_plan = round(bobot_plan, 2)
            else:
                record.progress_plan = 0.0
    
    @api.depends('wbs_ids')
    def _get_actual_progress(self):
        for record in self:
            # if record.project:
            #     start_date = record.project.date_start

            #     progres = self.env['task.progress'].search([
            #         ('project', '=', record.project.id),
            #         ('date', '>=', start_date),
            #         ('date', '<=', record.date)
            #     ])

            #     bobot_actual = sum(progres.mapped('actual_weight'))

            #     record.progress_actual = round(bobot_actual, 2)
            # else:
            #     record.progress_actual = 0.0
            actual_weight = 0.0
            if record.wbs_ids:
                for data in record.wbs_ids:
                    actual_weight += data.total_actual

                record.progress_actual = round(actual_weight, 2)

                _logger.info({actual_weight})


    @api.depends('progress_plan', 'progress_actual')
    def _get_deviasi(self):
        for record in self:
            selisih = record.progress_actual - record.progress_plan
            record.deviasi = round(selisih, 2)

    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(DailyReport, self).write(vals)
    
    def action_confirm_all(self):
        # Mengambil semua record yang terpilih
        selected_records = self.browse(self.env.context.get('active_ids'))

        # Mengubah status menjadi 'confirmed' untuk setiap record terpilih
        for record in selected_records:
            if record.status != 'confirm':  # Pastikan hanya mengubah status jika belum 'confirm'
                record.status = 'confirm'
                record.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def _get_related_documents(self):
        document_reports = self.env['document.report'].search([('daily_report', '=', self.id)])
        return document_reports

    def get_document_reports(self):
        return self._get_related_documents()

    def action_view_document_report(self):
        self.ensure_one()
        return {
            'name': 'Document Report',
            'domain': [('daily_report', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'document.report',
            'type': 'ir.actions.act_window',
            'context': {'default_daily_report': self.id},
        }

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body="Confirmed by %s" % (self.env.user.name))

        self.wbs_ids.action_confirm()
        # for wbs_record in self.wbs_ids:
        #     wbs_record.action_confirm()
        #     wbs_record.total_progress = sum(
        #     progress.progress for progress in self.env['task.progress'].search([
        #         ('task_id', '=', wbs_record.wbs.id)
        #     ])
        # )

    def action_canceled(self):
        self.status = 'draft'
        self.message_post(body="Cancelled by %s" % (self.env.user.name))

    def action_done(self):
        self.status = 'done'
        self.message_post(body="Done by %s" % (self.env.user.name))

    @api.depends('project')
    def _get_name_mp(self):
        for record in self:
            if record.project:

                manpower_ids = record.project.manpower_ids

                name_mp = []
                for i in manpower_ids:
                    name_mp.append(i.id)
                record.name_mp_ids = name_mp
            
            else:
                record.name_mp_ids = []

    def action_refresh(self):
        """Method to refresh project-related fields"""
        for record in self:
            record.leader = False
            record.supervisor = False
            record.note_ids.name_mp = False
            record.note_ids._get_name_mp()
            record.manpower_ids = [(5, 0, 0)]
            record._depends_project()
            record.manpower_ids._compute_amount
            record.wbs_ids = [(5, 0, 0)]
            record._get_task()

    @api.model
    def create(self, vals):
        if 'date' in vals:
            existing_report = self.env['daily.report'].search([
                ('date', '=', vals['date']),
                ('project', '=', vals.get('project'))
            ])
            if existing_report:
                raise exceptions.ValidationError(
                    "Daily Report untuk tanggal %s sudah tersedia." % vals['date']
                )
        if vals.get('no_dr', 'New') == 'New':
            vals['no_dr'] = self.env['ir.sequence'].next_by_code('no.dr') or 'New'
        
        result = super(DailyReport, self).create(vals)
        return result
    
    @api.depends('project')
    def _depends_project(self):
        if self.project:
            project = self.project

            manpower_records = []
            added_job_titles = set()
            for record in project:
                for manpower in record.manpower_ids:
                    if manpower.job_title not in added_job_titles:
                        manpower_records.append((0, 0, {
                            'job_title': manpower.job_title,
                            'amount': 0,
                            'location': ''
                        }))
                        added_job_titles.add(manpower.job_title)
            self.manpower_ids = manpower_records
        else:
            self.manpower_ids = [(5, 0, 0)]

    @api.depends('project')
    def _get_task(self):
        for report in self:
            if report.project:
                tasks = report.project.task_ids
                wbs_list = []

                for task in tasks:
                    # Menghitung total plan_weight dari semua progress_ids
                    total_plan_weight = sum(progress.plan_weight for progress in task.progress_ids) if task.progress_ids else 0.0
                    total_progress = task.total_progress
                    # total_progress = task._get_total_progress()

                    wbs_list.append((0, 0, {
                        'wbs': task.id,
                        'wbs_category': task.wbs_category.id,
                        'plan_weight': total_plan_weight,
                        'actual_weight': 0.0,
                        'total_progress': total_progress,
                    }))
                report.wbs_ids = wbs_list
            else:
                report.wbs_ids = False
    
    # def get_table_b_c_filler(self):
    #     """
    #     Menghitung berapa banyak baris kosong yang perlu ditambahkan ke Tabel B dan C,
    #     sehingga jumlah baris B dan C sama dan total barisnya sesuai dengan Tabel A.
    #     """
    #     jumlah_baris_a = len(self.wbs_ids)
    #     jumlah_baris_b = len(self.mos_ids)
    #     jumlah_baris_c = len(self.equipment_ids)

    #     # Hitung total baris yang ada di B dan C saat ini
    #     total_baris_b_c = jumlah_baris_b + jumlah_baris_c

    #     # Hitung selisih baris antara A dan total B + C
    #     total_rows_to_fill = jumlah_baris_a - total_baris_b_c

    #     if total_rows_to_fill > 0:
    #         # Bagi sisa baris yang perlu ditambahkan secara proporsional antara B dan C
    #         target_total_b_c = max(jumlah_baris_b, jumlah_baris_c) + (total_rows_to_fill // 2)
    #         rows_for_b = target_total_b_c - jumlah_baris_b
    #         rows_for_c = target_total_b_c - jumlah_baris_c
    #     else:
    #         rows_for_b = 0
    #         rows_for_c = 0

    #     return rows_for_b, rows_for_c

class WBS(models.Model):
    _name = 'wbs.dr'

    daily_report_id = fields.Many2one('daily.report', string="Daily Report")
    wbs_category = fields.Many2one('wbs.category', string='WBS Category')
    wbs = fields.Many2one('project.task', string='WBS', domain="[('project_id', '=', project_id)]")
    plan_weight = fields.Float(string="Plan Weight")
    actual_weight = fields.Float(string="Actual Weight", compute='_get_actual_weight')
    progress = fields.Float(string="Progress (%)")
    total_progress = fields.Float(string="Total Progress (%)", readonly=True, compute="_onchange_progress")
    total_actual = fields.Float(string="Bobot Aktual", invisible=True, compute="_get_total_actual")
    project_id = fields.Many2one('project.project', string='Project', related='daily_report_id.project', store=True)
    is_highlighted = fields.Boolean(
            compute="_compute_is_highlighted",
            string="Highlighted"
        )

    def _compute_is_highlighted(self):
        for record in self:
            task_start_date = record.wbs.start_date.date()
            task_end_date = record.wbs.end_date.date()
            if record.daily_report_id.date and task_start_date and task_end_date:
                record.is_highlighted = task_start_date <= record.daily_report_id.date <= task_end_date
            else:
                record.is_highlighted = False
    # previous_progress = fields.Float(string="Previous Progress", compute="_compute_previous_progress", store=True)

    # @api.depends('progress')
    # def _compute_previous_progress(self):
    #     for record in self:
    #         record.previous_progress = record.progress  # Menyimpan nilai progress sebelumnya

    @api.depends('plan_weight', 'total_progress')
    def _get_total_actual(self):
        for record in self:
            if record.plan_weight and record.total_progress:
                weight = record.plan_weight / 100
                record.total_actual = weight * record.total_progress
            else: 
                record.total_actual = 0

    @api.depends('plan_weight','progress')
    def _get_actual_weight(self):
        for record in self:
            if record.plan_weight and record.progress:
                weight = record.plan_weight / 100
                record.actual_weight = weight * record.progress
            else: 
                record.actual_weight = 0
    
    # update terakhir
    @api.depends('progress')
    def _onchange_progress(self):
        for record in self:
            current_total_progress = record.wbs.total_progress or 0

            # Cari apakah ada task_progress yang sudah ada
            task_progress = self.env['task.progress'].search([
                ('date', '=', record.daily_report_id.date),
                ('project', '=', record.daily_report_id.project.id),
                ('task_id', '=', record.wbs.id)
            ], limit=1)
            
            if task_progress:  # Jika task_progress sudah ada
                # Ambil progress lama
                previous_progress = task_progress.progress
                # Hitung total progress baru
                new_total_progress = current_total_progress - previous_progress + record.progress
            else:  # Jika task_progress belum ada
                # Total progress hanya ditambahkan langsung
                new_total_progress = current_total_progress + record.progress

            # Validasi agar total progress tidak melebihi 100%
            if new_total_progress > 100:
                raise ValidationError("Total progress kumulatif tidak boleh melebihi 100%. Mohon periksa input Anda.")

            # Perbarui total_progress
            record.total_progress = new_total_progress
    
    def action_confirm(self):
        for record in self:
            if record.progress >= 100:
                raise ValidationError("Total progress tidak boleh melebihi 100%. Mohon periksa input Anda.")
            else:
                task_progress = self.env['task.progress'].search([
                    ('date', '=', record.daily_report_id.date),
                    ('project', '=', record.daily_report_id.project.id),
                    ('task_id', '=', record.wbs.id)
                ], limit=1)

                if task_progress:
                    cumulative_progress = task_progress.task_id.total_progress - task_progress.progress + record.progress

                    if cumulative_progress > 100:
                        raise ValidationError("Progress kumulatif untuk task ini akan melebihi 100%. Mohon periksa input Anda.")
                    else:    
                        task_progress.progress = record.progress 
                        task_progress.actual_weight = record.actual_weight
                        # record.wbs.total_progress = cumulative_progress
                else:
                    if record.progress > 0:
                        previous_task_progress = self.env['task.progress'].search([
                            ('project', '=', record.daily_report_id.project.id),
                            ('task_id', '=', record.wbs.id)
                        ], order='date desc', limit=1)

                        all_task_progress = self.env['task.progress'].search([
                            ('project', '=', record.daily_report_id.project.id),
                            ('task_id', '=', record.wbs.id)
                        ])
                        number_of_existing_rows = len(all_task_progress)

                        if record.wbs.total_progress + record.progress > 100:
                            raise ValidationError(
                                "Progress kumulatif untuk task ini akan melebihi 100%. Mohon periksa input Anda."
                            )

                        if previous_task_progress:
                            self.env['task.progress'].create({
                                'date': record.daily_report_id.date,
                                'project': record.daily_report_id.project.id,
                                'task_id': record.wbs.id,
                                'plan_b': previous_task_progress.plan,  
                                'plan_weight_b': record.wbs.task_weight / (number_of_existing_rows + 1),  
                                'progress': record.progress,  
                                'actual_weight': record.actual_weight 
                            })
                        # record.wbs.total_progress = record.wbs.total_progress + record.progress
                
            # if record.wbs:
            #     record.wbs.task_id.get_total_progress()
                        
                
class MaterialonSite(models.Model):
    _name = 'mos.dr'

    daily_report_id = fields.Many2one('daily.report', string="Daily Report")
    product = fields.Many2one('product.template', string='Product', domain="[('rab_category', '=', 'material')]")
    volume = fields.Float(string="Volume")
    uom = fields.Many2one('uom.uom', string="UoM")
    origin_location = fields.Char(string="Origin Location")
    destination_location = fields.Char(string="Destination Location")

class EquipmentUsed(models.Model):
    _name = 'equipment.dr'

    daily_report_id = fields.Many2one('daily.report', string="Daily Report")
    product = fields.Many2one('product.template', string="Product", domain="[('id', 'in', product_ids)]")
    amount = fields.Integer(string="Amount")
    location = fields.Char(string="Location")        

    product_ids = fields.Many2many('product.template', compute='_get_equipment', string="Available Products", store=False) 

    @api.depends('daily_report_id.project')
    def _get_equipment(self):
        for x in self:
            if x.daily_report_id.project:

                rab_records = self.env['budget.plan'].search([('project', '=', x.daily_report_id.project.id)])

                for rab in rab_records:
                    ahs = rab.boq.boq_mk_ids.ahs.ahs_equipment_ids
                    product_ids = []
                    for equipment in ahs:
                        if equipment.product and equipment.product.rab_category == 'equipment':
                            product_ids.append(equipment.product.id)
                    x.product_ids = product_ids
            else:
                x.product_ids = []

class Manpower(models.Model):
    _name = 'manpower.dr'

    daily_report_id = fields.Many2one('daily.report', string="Daily Report")
    job_title = fields.Char(string="Job Title")
    amount = fields.Integer(string="Amount", compute="_compute_amount")
    location = fields.Char(string="Location")

    def _compute_amount(self):
        for record in self:
            if record.daily_report_id and record.daily_report_id.date:
                report_date = record.daily_report_id.date
                start_of_day = datetime.combine(report_date, datetime.min.time())
                end_of_day = datetime.combine(report_date, datetime.max.time())

                manpower_ids = record.daily_report_id.project.manpower_ids.ids
                project = record.daily_report_id.project.id
                
                attendance_records = self.env['hr.attendance'].search([
                    ('employee_id', 'in', manpower_ids),
                    ('check_in', '>=', start_of_day),
                    ('check_in', '<=', end_of_day),
                    ('check_out', '!=', False),
                    ('project_name', '=', project)
                ])
                record.amount = len(attendance_records.filtered(lambda r: r.employee_id.job_title == record.job_title))
            else:
                record.amount = 0

class Weather(models.Model):
    _name = 'weather.dr'

    daily_report_id = fields.Many2one('daily.report', string="Daily Report")
    weather = fields.Many2one('field.condition.type', string="Weather")
    started_time = fields.Float(string="Started Time")
    ended_time = fields.Float(string="Ended Time")
    location = fields.Char(string="Location")
    # responsibility = fields.Char(string="Responsibility")
    result = fields.Char(string="Result")

class Note(models.Model):
    _name = 'note.dr'

    daily_report_id = fields.Many2one('daily.report', string="Daily Report")
    note_point = fields.Char('Note Point')
    desc = fields.Text('Description')
    name_mp = fields.Many2one('hr.employee', string="Name", domain="[('id', 'in', name_mp_ids)]")
    name_mp_ids = fields.Many2many('hr.employee', compute='_get_name_mp', store=False)

    @api.depends('daily_report_id.project')
    def _get_name_mp(self):
        for record in self:
            if record.daily_report_id and record.daily_report_id.project:

                manpower_ids = record.daily_report_id.project.manpower_ids
 
                name_mp = []
                for i in manpower_ids:
                    name_mp.append(i.id)
                record.name_mp_ids = name_mp
            
            else:
                record.name_mp_ids = []

class Monitoring(models.Model):
    _name = 'monitoring.dr'

    daily_report_id = fields.Many2one('daily.report', string="Daily Report")
    pdf_file = fields.Binary(string='PDF File', attachment=True)
    pdf_image = fields.Image(string='PDF as Image', compute='_compute_pdf_image')

    @api.depends('pdf_file')
    def _compute_pdf_image(self):
        for record in self:
            if record.pdf_file:
                try:
                    # Decode PDF file from base64
                    pdf_data = base64.b64decode(record.pdf_file)

                    # Convert PDF to image (first page only)
                    images = convert_from_bytes(pdf_data, first_page=0, last_page=1)
                    if images:
                        # Convert the image to PNG format and save as binary
                        img = images[0]
                        byte_io = BytesIO()
                        img.save(byte_io, format='PNG')
                        byte_io.seek(0)
                        record.pdf_image = base64.b64encode(byte_io.read())
                    else:
                        record.pdf_image = False
                except Exception as e:
                    _logger = logging.getLogger(__name__)
                    _logger.error("Error converting PDF to image: %s", e)
                    record.pdf_image = False
            else:
                record.pdf_image = False
    def print_report(self):
        return self.env.ref('fits_management_construction.report_daily_report_template').report_action(self)
    @api.model
    def get_pdf_url(self):
        if not self.pdf_file:
            return False
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('name', '=', 'pdf_filename.pdf')
        ], limit=1)
        if attachment:
            return '/web/content/{}?download=true'.format(attachment.id)
        return False