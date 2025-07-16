# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    start_date = fields.Datetime(sting='Started Date')
    end_date = fields.Datetime(sting='Ended Date')
    task_cost = fields.Float(string='Task Cost')
    task_weight = fields.Float(string='Task Weight (%)', compute='_get_task_weight')
    actual_weight = fields.Float(string='Actual Weight (%)', compute='_get_actual_weight')
    total_progress = fields.Float(string='Total Progress (%)', compute='_get_total_progress', store=True)
    progress_ids = fields.One2many('task.progress', 'task_id', string='Progress')
    wbs_category = fields.Many2one('wbs.category', string="WBS Category")

    def action_generate_progress_dates(self):
        self.generate_progress_dates()

    @api.depends('task_cost', 'project_id.total_cost') 
    def _get_task_weight(self):
        for record in self:
            if record.project_id and record.project_id.total_cost:
                record.task_weight = (record.task_cost / record.project_id.total_cost) * 100
            else:
                record.task_weight = 0
    
    @api.depends('progress_ids.actual_weight')
    def _get_actual_weight(self):
        for record in self:
            total_actual_weight = sum(record.progress_ids.mapped('actual_weight'))
            record.actual_weight = total_actual_weight
    
    @api.depends('progress_ids.progress')
    def _get_total_progress(self):
        for record in self:
            total_progress = sum(record.progress_ids.mapped('progress'))
            record.total_progress = total_progress

    def generate_progress_dates(self):
        """Generate progress records with dates between start_date and end_date."""
        for task in self:
            if task.start_date and task.end_date:
                task.progress_ids.unlink()

                start_date = task.start_date.date()
                end_date = task.end_date.date()
                total_days = (end_date - start_date).days + 1 
                
                if total_days <= 0:
                    continue  

                daily_plan = 100.0 / total_days
                daily_plan_weight = self.task_weight / total_days

                current_date = start_date
                while current_date <= end_date:
                    self.env['task.progress'].create({
                        'date': current_date,
                        'task_id': task.id,
                        'project': task.project_id.id,
                        'plan': daily_plan,
                        'plan_b': 0.0,  
                        'progress': 0.0,  
                        'plan_weight': daily_plan_weight,  
                        'plan_weight_b': 0.0,   
                        'actual_weight': 0.0,  
                    })
                    current_date += timedelta(days=1)

class TaskProgress(models.Model):
    _name = 'task.progress'

    date = fields.Date(string='Date')
    project = fields.Many2one('project.project', string='Project')
    plan = fields.Float(string='Plan A (%)')
    plan_b = fields.Float(string='Plan B (%)')
    progress = fields.Float(string='Progress (%)')
    plan_weight = fields.Float(string='Plan Weight A (%)')
    plan_weight_b = fields.Float(string='Plan Weight B (%)')
    actual_weight = fields.Float(string='Actual Weight (%)', compute='_compute_actual_weight', store=True)
    task_id = fields.Many2one('project.task', string='Related Task', ondelete='cascade')

    @api.depends('plan_weight', 'plan_weight_b', 'progress')
    def _compute_actual_weight(self):
        for x in self:
            if x.plan_weight_b and x.progress:
                x.actual_weight = (x.progress * x.plan_weight_b) / 100
            elif x.plan_weight and x.progress:
                x.actual_weight = (x.progress * x.plan_weight) / 100
            else:
                x.actual_weight = 0
    
    def update_task_actual_weight(self):
        for record in self:
            task = record.task_id
            
            total_actual_weight = self.env['task.progress'].search([
                ('task_id', '=', task.id)
            ]).mapped('actual_weight')

            task.actual_weight = sum(total_actual_weight)

    # def get_last_updated_date_for_project(self, project_id):
    #     """
    #     Mengambil tanggal terakhir progress dari semua task di project ini.
    #     Jika tidak ada progress ditemukan, kembalikan start_date proyek.
    #     """

    #      # Cari progress terakhir dari semua task yang terkait dengan proyek ini
    #     progress_record = self.env['task.progress'].search([
    #         ('project', '=', project_id.id),  # Field 'project' merujuk ke proyek
    #         ('progress', '>', 0)             # Progress harus valid
    #     ], order="date desc", limit=1)

    #     # Jika ditemukan progress, kembalikan tanggalnya
    #     if progress_record:
    #         return progress_record.date

    #     # Jika tidak ada progress, kembalikan start_date proyek
    #     return project_id.start_date
