# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import datetime
import logging

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
                ['date:day']
            )
            # last_updated_date = self.get_last_updated_date_for_project()
            # last_updated_date = self.get_last_updated_date_for_project(x.project_id)
            # _logger.info(f"Last updated date for project {x.project_id.name}: {last_updated_date}")

            bobot_plan = 0
            bobot_plan_b = 0
            bobot_actual = 0

            for group in groups:
                print('>>>>>>', group['date:day'], group.get('plan_weight', 0), group.get('plan_weight_b', 0), group.get('actual_weight', 0))

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
                    "actual_weight": rec_bobot_actual  
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
        
        for line in curve_lines:
            dates.append(line.date.strftime('%Y-%m-%d'))
            plan_weights.append(line.plan_weight)
            actual_weights.append(line.actual_weight)
            
        return {
            'dates': dates,
            'plan_weights': plan_weights,
            'actual_weights': actual_weights,
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