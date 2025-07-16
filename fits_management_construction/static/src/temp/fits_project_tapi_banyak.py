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

            # Logging hasil
            for key, value in grouped_wbs.items():
                _logger.info(
                    f"Key: {key}, Start Date: {value['start_date']}, End Date: {value['end_date']}, "
                    f"WBS Category: {value['wbs_category']}, WBS Names: {value['wbs_names']}, "
                    f"Progress Dates: {value['progress_dates']}"
                )

            ## Dictionary untuk menyimpan hasil grouping berdasarkan task_id
            # grouped_wbs = {}

            # for progress in progress_records:
            #     task = progress.task_id
            #     if not task:
            #         continue

            #     # Ambil start_date dan end_date dari task
            #     start_date = task.start_date
            #     end_date = task.end_date

            #     # Pastikan task hanya diambil dalam rentang tanggal yang valid
            #     if start_date and end_date and (x.start_date <= start_date.date() <= x.end_date):
            #         # project_id = task.project_id.id
            #         # project_name = task.project_id.name
            #         wbs_category = task.wbs_category.wbs_category

            #         # Ambil semua WBS yang sesuai dari task
            #         # wbs_names = task.mapped('display_name')

            #         # Kelompokkan berdasarkan task_id untuk menghindari duplikasi
            #         if task.id not in grouped_wbs:
            #             grouped_wbs[task.id] = {
            #                 'wbs_category': wbs_category,
            #                 'wbs_names': task.display_name,
            #                 'start_date': start_date,
            #                 'end_date': end_date,
            #             }

            # # Log hasil yang sudah dikelompokkan
            # for data in grouped_wbs.items():
            #     _logger.info(f"Start Date: {data['start_date']}, End Date: {data['end_date']}, "
            #                 f"WBS Category: {data['wbs_category']}, "
            #                 f"WBS Names: {data['wbs_names']}")

            # # Logging
            # _logger.info(f"Group Date: {date}, Project ID: {project_id}")
            # task_project = self.env['project.task'].search([('project_id', '=', x.project_id.id)])
            # wbs_name = task_project.wbs_category.wbs_ids.name.product_variant_id
            # _logger.info(f"WBS CATEGORY : {task_project.wbs_category.wbs_category}")
            # # _logger.info(f"WBS Name : {wbs_name.name}")
            # for wbs in wbs_name:
            #     _logger.info(f"WBS Name: {wbs.name}")
            
            # data_wbs = {}

            # # Mencari project.task terkait
            # task_project = self.env['project.task'].search([('project_id', '=', x.project_id.id)])

            # # Mengambil wbs_category dan wbs_names
            # wbs_categories = task_project.mapped('wbs_category')  # Memetakan wbs_category dari task_project
            # for wbs_category in wbs_categories:
            #     wbs_names = wbs_category.mapped('wbs_ids.name.product_variant_id')  # Memetakan wbs names dari wbs_category
            #     # Menyimpan wbs_category dan wbs names dalam dictionary
            #     data_wbs[wbs_category.wbs_category] = [wbs.name for wbs in wbs_names]

            # # Logging untuk memeriksa hasil
            # # _logger.info(f"Data WBS Category and WBS: {data_wbs}")

            # for wbs_category, wbs_list in data_wbs.items():
            #     data = {
            #         "curve_id": self.id,
            #         "wbs_category": wbs_category,
            #         "wbs": ', '.join(wbs_list),  # Gabungkan WBS names menjadi string
            #         # Tambahkan field lainnya jika diperlukan, seperti task_id atau project_id
            #     }

            #     x.line_ids.create(data)

            bobot_plan = 0
            bobot_plan_b = 0
            bobot_actual = 0
            
            # _logger.info(f"Task Name : {groups}")
            # task_progress = progres.search([('project', '=', x.project_id.id)])
            # _logger.info(f"Task Progress : {progres.task_id.wbs_category.wbs_category} - {progres.task_id.name} - {progres.task_id.project_id.name}")


            for group in groups:
                # print('>>>>>>', group['date:day'], group.get('plan_weight', 0), group.get('plan_weight_b', 0), group.get('actual_weight', 0), group.get('task_id', ''))
                # task = self.env['project.task'].browse(task_id[0])

                date_str = group['date:day']
                try:
                    date_obj = datetime.strptime(date_str, '%d %b %Y')
                    formatted_date = date_obj.strftime('%Y-%m-%d') 
                except ValueError as e:
                    print(f"Error converting date: {e}")
                    continue

                rec_bobot_plan = bobot_plan + group.get('plan_weight', 0)
                rec_bobot_plan_b = bobot_plan_b + group.get('plan_weight_b', 0)
                rec_bobot_actual = bobot_actual + group.get('actual_weight', 0)

                data = {
                    "curve_id": self.id,
                    "date": formatted_date,
                    "plan_weight": rec_bobot_plan,
                    "plan_weight_b": rec_bobot_plan_b,
                    "actual_weight": rec_bobot_actual,
                    # "wbs_category": wbs_category.name,
                    # "wbs": ', '.join(wbs_names),
                }
                x.line_ids.create(data)
                bobot_plan = rec_bobot_plan
                bobot_plan_b = rec_bobot_plan_b
                bobot_actual = rec_bobot_actual

            x.plan_weight = bobot_plan
            x.plan_weight_b = bobot_plan_b
            x.actual_weight = bobot_actual  
            x.deviasi = x.actual_weight - x.plan_weight  
 
    def get_curve_s_data(self):
        self.ensure_one()
        curve_lines = self.line_ids.sorted(key=lambda r: r.date)
        
        dates = []
        plan_weights = []
        actual_weights = []
        # wbs_data = {}
        
        for line in curve_lines:
            dates.append(line.date.strftime('%Y-%m-%d'))
            plan_weights.append(line.plan_weight)
            actual_weights.append(line.actual_weight)
            # category_name = line.wbs_category
            # wbs_list = line.wbs.split(',')  # Split WBS jika disimpan dalam string
            # if category_name not in wbs_data:
            #     wbs_data[category_name] = set(wbs_list)  # Gunakan set untuk menghindari duplikasi
            # else:
            #     wbs_data[category_name].update(wbs_list)
        
        # wbs_categories = [
        #     {
        #         'category_name': category,
        #         'wbs': list(wbs_list)
        #     }
        #     for category, wbs_list in wbs_data.items()
        # ]

        # _logger.info(f"Final WBS Categories: {wbs_categories}")
            
        return {
            'dates': dates,
            'plan_weights': plan_weights,
            'actual_weights': actual_weights,
            # 'wbs_categories': wbs_categories,
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
    # wbs_category = fields.Char(string='WBS Category')
    # wbs = fields.Text(string='WBS Names')