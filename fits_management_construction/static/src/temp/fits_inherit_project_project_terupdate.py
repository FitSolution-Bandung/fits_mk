# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import datetime
import logging
from collections import defaultdict

_logger = logging.getLogger(__name__)

class ProjectProject(models.Model):
    _inherit = 'project.project'

    budget_plan_count = fields.Integer(string='Budget Plans', compute='_compute_budget_plan_count')

    def _compute_budget_plan_count(self):
        for project in self:
            project.budget_plan_count = self.env['budget.plan'].search_count([('project', '=', project.id),('status', '=', 'confirm')])

    def action_view_budget_plans(self):
        self.ensure_one()
        return {
            'name': 'Budget Plans',
            'domain': [('project', '=', self.id),('status', '=', 'confirm')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'budget.plan',
            'type': 'ir.actions.act_window',
            'context': {'default_project': self.id},
        }
    
    boq_count = fields.Integer(string='Bill of Quantity', compute='_compute_boq_count')

    def _compute_boq_count(self):
        for project in self:
            project.boq_count = self.env['boq'].search_count([('project', '=', project.id),('status', '=', 'confirm')])

    def action_view_boqs(self):
        self.ensure_one()
        return {
            'name': 'Bill of Quantity',
            'domain': [('project', '=', self.id),('status', '=', 'confirm')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'boq',
            'type': 'ir.actions.act_window',
            'context': {'default_project': self.id},
        }
    
    def action_view_curve_s(self):
        self.ensure_one()
        return {
            'name': 'S-Curve',
            'domain': [('project_id', '=', self.id)],
            'view_mode': 'tree,form',
            'res_model': 'project.curve.s',
            'type': 'ir.actions.act_window',
            'context': {'default_project_id': self.id},
        }
    
    contract_date = fields.Char(string='Contract Number/Date')
    smpk_date = fields.Char(string='SMPK Number/Date')
    provider = fields.Many2one('res.partner', string='Provider')
    supervisory_consultant = fields.Many2one('res.partner' ,string='Supervsisory Consultant')
    planning_consultant = fields.Many2one('res.partner', string='Planning Consultant')
    total_cost = fields.Float(string='Total Cost')
    progress_project = fields.Float(string='Progress Project')

    def update_progress_project(self):
        for project in self:
            progres = self.env['task.progress']
            groups = progres.read_group([('project', '=', project.id)], ['actual_weight'], ['project'])
            
            total_actual_weight = 0
            for group in groups:
                total_actual_weight += group.get('actual_weight', 0)

            project.progress_project = total_actual_weight

    def refresh_progress_project(self):
        self.update_progress_project()

class ProjectCurveS(models.Model):
    _name = 'project.curve.s'
    _description = 'S Curve'
    _rec_name ='project_id'

    # curve_id = fields.Integer('Curve Id')
    project_id = fields.Many2one('project.project', string="Project")
    start_date = fields.Date(string="Start Date", compute='_compute_dates', store=True)
    end_date = fields.Date(string="End Date", compute='_compute_dates', store=True)
    total_planned = fields.Float(string='Total Planned (%)')
    total_actual = fields.Float(string='Total Actual (%)')
    plan_weight = fields.Float(string='Total Plan Weight(%)')
    plan_weight_b = fields.Float(string='Total Plan B Weight(%)')
    actual_weight = fields.Float(string='Total Actual Weight (%)')
    deviasi = fields.Float(string='Deviasi (%)')
    line_ids = fields.One2many('curve.s.line', 'curve_id', string='S Curve Line')

    @api.depends('project_id')
    def _compute_dates(self):
        for record in self:
            if record.project_id:
                record.start_date = record.project_id.date_start
                record.end_date = record.project_id.date
            else:
                record.start_date = False
                record.end_date = False
    
    def show_curva(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'curve_s_chart',
            'name': f'S Curve - {self.project_id.name}',
            'target': 'new',
            'context': {
                'active_id': self.id,
            },
        }
    
    def get_last_updated_date_for_project(self):
        self.ensure_one()

        progress_record = self.env['task.progress'].search([
            ('task_id.project_id', '=', self.project_id.id),
            ('progress', '>', 0)
        ], order="date desc", limit=1)

        if progress_record:
            return progress_record.date
        
        return self.project_id.date_start

    def calculate_progress(self):
        for x in self:
            x.line_ids = [(5, 0, 0)]
            progres = self.env['task.progress']
            groups = progres.read_group(
                [('project', '=', x.project_id.id), ('date', '>=', x.start_date), ('date', '<=', x.end_date)],
                ['date', 'plan_weight', 'plan_weight_b', 'actual_weight'],
                ['date:day'],
            )
            
            # Cari progress berdasarkan project dan rentang tanggal yang diinput
            progress_records = progres.search([
                ('project', '=', x.project_id.id),
                ('date', '>=', x.start_date),
                ('date', '<=', x.end_date)
            ])

            grouped_wbs = defaultdict(lambda: {
                'wbs_category': '',
                'wbs_names': '',
                'start_date': '',
                'end_date': '',
                'progress_dates': []
            })

            processed_wbs_names = set()

            for task in progress_records:  # tasks adalah kumpulan task yang Anda iterasi
                task_start_date = task.task_id.start_date
                task_end_date = task.task_id.end_date

                # Pastikan WBS belum diproses sebelumnya
                if task.task_id.display_name in processed_wbs_names:
                    continue  # Skip jika sudah diproses
                
                # Tambahkan WBS ke set
                processed_wbs_names.add(task.task_id.display_name)

                # Cari progress dalam rentang start_date - end_date
                progress_records = self.env['task.progress'].search([
                    ('task_id', '=', task.task_id.id),
                    ('date', '>=', task_start_date),
                    ('date', '<=', task_end_date)
                ])
                
                # # Jika WBS name sudah ada di grouped_wbs, lewati iterasi ini
                wbs_name = task.task_id.display_name
                # if wbs_name not in grouped_wbs:
                    # Menampung tanggal dengan progress > 0 (tetap dihitung, tapi tidak duplikat)
                progress_dates = [progress.date for progress in progress_records if progress.progress > 0]

                # Simpan hanya satu entri per WBS name
                grouped_wbs[task.id] = {
                    'wbs_category': task.task_id.wbs_category.wbs_category,
                    'wbs_names': wbs_name,
                    'start_date': task_start_date,
                    'end_date': task_end_date,
                    'progress_dates': progress_dates
                }

            # # Logging hasil
            # for key, value in grouped_wbs.items():
            #     _logger.info(
            #         f"Key: {key}, Start Date: {value['start_date']}, End Date: {value['end_date']}, "
            #         f"WBS Category: {value['wbs_category']}, WBS Names: {value['wbs_names']}, "
            #         f"Progress Dates: {value['progress_dates']}"
            #     )

            bobot_plan = 0
            bobot_plan_b = 0
            bobot_actual = 0

            for group in groups:
                date_str = group['date:day']
                try:
                    date_obj = datetime.strptime(date_str, '%d %b %Y')
                    formatted_date = date_obj.date()
                except ValueError as e:
                    print(f"Error converting date: {e}")
                    continue

                rec_bobot_plan = bobot_plan + group.get('plan_weight', 0)
                rec_bobot_plan_b = bobot_plan_b + group.get('plan_weight_b', 0)
                rec_bobot_actual = bobot_actual + group.get('actual_weight', 0)

                # Cari WBS terkait tanggal ini
                wbs_data = []
                for key, value in grouped_wbs.items():
                    # Cek apakah tanggal termasuk dalam rentang start_date dan end_date
                    plan_date = None
                    start_date_task = value['start_date'].date()
                    end_date_task = value['end_date'].date()
                    if start_date_task <= formatted_date <= end_date_task:
                        plan_date = formatted_date

                    # Cek apakah tanggal cocok dengan progress_dates
                    actual_date = None
                    if formatted_date in value['progress_dates']:
                        actual_date = formatted_date

                    # Jika ada data yang cocok
                    if plan_date or actual_date:
                        wbs_data.append({
                            'wbs_category': value['wbs_category'],
                            'wbs_names': value['wbs_names'],
                            'plan_date': plan_date,
                            'actual_date': actual_date,
                            'start_date': value['start_date'],
                            'end_date': value['end_date']
                        })

                # Gabungkan data S Curve dengan Gantt Chart
                data = {
                    "curve_id": self.id,
                    "date": formatted_date,
                    "plan_weight": rec_bobot_plan,
                    "plan_weight_b": rec_bobot_plan_b,
                    "actual_weight": rec_bobot_actual,
                    "wbs_category": ','.join([wbs['wbs_category'] for wbs in wbs_data]),
                    "wbs_names": ','.join([wbs['wbs_names'] for wbs in wbs_data]),
                    "plan_date": ','.join(
                        [wbs['plan_date'].strftime('%Y-%m-%d') for wbs in wbs_data if wbs['plan_date']]
                    ),
                    "actual_date": ','.join(
                        [wbs['actual_date'].strftime('%Y-%m-%d') for wbs in wbs_data if wbs['actual_date']]
                    ),
                    'start_date': start_date_task,
                    'end_date': end_date_task
                }

                # Buat record ke model
                x.line_ids.create(data)
                bobot_plan = rec_bobot_plan
                bobot_plan_b = rec_bobot_plan_b
                bobot_actual = rec_bobot_actual

            # Update nilai akhir ke objek utama
            x.plan_weight = bobot_plan
            x.plan_weight_b = bobot_plan_b
            x.actual_weight = bobot_actual  
            x.deviasi = x.actual_weight - x.plan_weight
            
    def get_curve_s_data(self):
        self.ensure_one()
        curve_lines = self.line_ids.sorted(key=lambda r: r.date)
        
        # Data untuk S Curve
        dates = []
        plan_weights = []
        actual_weights = []
        wbs_category = []
        wbs_name = []
        plan_date = []
        actual_date = []
        start_date = []
        end_date = []

        # Menyaring dan memproses data berdasarkan tipe (S Curve atau Gantt Chart)
        for line in curve_lines:
                # Data untuk S Curve
                dates.append(line.date.strftime('%Y-%m-%d'))
                plan_weights.append(line.plan_weight)
                actual_weights.append(line.actual_weight)

                wbs_category.append(line.wbs_category.split(','))
                wbs_name.append(line.wbs_names.split(','))  # Menambahkan WBS Names
                plan_date.append(line.plan_date.split(',') if line.plan_date else None)  # Menambahkan Start Date
                actual_date.append(line.actual_date.split(',') if line.actual_date else None)  # Menambahkan End Date
                start_date.append(line.start_date.strftime('%Y-%m-%d'))  # Menambahkan Start Date
                end_date.append(line.end_date.strftime('%Y-%m-%d'))  # Menambahkan End Date

        return {
            'dates': dates,
            'plan_weights': plan_weights,
            'actual_weights': actual_weights,
            'wbs_category': wbs_category,
            'wbs_name': wbs_name,
            'plan_date': plan_date,
            'actual_date': actual_date,
            'start_date': start_date,
            'end_date': end_date
        }
    
class CurveSLine(models.Model):
    _name = 'curve.s.line'
    
    curve_id = fields.Many2one('project.curve.s', string='S Curve', ondelete='cascade')
    date = fields.Date('Date')
    task_id = fields.Many2one('project.task', string='Task')
    project_id = fields.Many2one('project.project',string='Project')
    plan_weight = fields.Float(string='Plan Weight (%)')
    plan_weight_b = fields.Float(string='Plan B Weight (%)')
    actual_weight = fields.Float(string='Actual Weight (%)')
    wbs_category = fields.Text(string='WBS Category')
    wbs_names = fields.Text(string='WBS Names')  # Menyimpan daftar WBS
    plan_date = fields.Text(string="Plan Date")
    actual_date = fields.Text(string="Actual Date")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    # progress_dates = fields.Text(string='Progress Dates')  # Daftar tanggal progress
    # data_type = fields.Selection([
    #     ('gantt', 'Gantt Chart'),
    #     ('s_curve', 'S Curve'),
    # ], string='Data Type', required=True, default='s_curve')
    
    # wbs_category = fields.Char(string='WBS Category')
    # wbs = fields.Text(string='WBS Names')