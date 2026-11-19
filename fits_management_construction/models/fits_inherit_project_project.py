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
            'view_mode': 'list,form',
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
            'view_mode': 'list,form',
            'res_model': 'boq',
            'type': 'ir.actions.act_window',
            'context': {'default_project': self.id},
        }
    
    def action_view_curve_s(self):
        self.ensure_one()
        return {
            'name': 'S-Curve',
            'domain': [('project_id', '=', self.id)],
            'view_mode': 'list,form',
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
        TaskProgress = self.env['task.progress']
        for project in self:
            [(total,)] = TaskProgress._read_group(
                [('project', '=', project.id)], aggregates=['actual_weight:sum'])
            project.progress_project = total or 0.0

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
        """Rebuild the cumulative S-curve lines (plan A, plan B, actual) per day."""
        TaskProgress = self.env['task.progress']
        for curve in self:
            curve.line_ids = [(5, 0, 0)]
            domain = [('project', '=', curve.project_id.id)]
            if curve.start_date:
                domain.append(('date', '>=', curve.start_date))
            if curve.end_date:
                domain.append(('date', '<=', curve.end_date))
            groups = TaskProgress._read_group(
                domain,
                groupby=['date:day'],
                aggregates=['plan_weight:sum', 'plan_weight_b:sum', 'actual_weight:sum'],
                order='date:day',
            )
            plan = plan_b = actual = 0.0
            lines = []
            for day, day_plan, day_plan_b, day_actual in groups:
                if not day:
                    continue
                plan += day_plan or 0.0
                plan_b += day_plan_b or 0.0
                actual += day_actual or 0.0
                lines.append({
                    'curve_id': curve.id,
                    'project_id': curve.project_id.id,
                    'date': day,
                    'plan_weight': plan,
                    'plan_weight_b': plan_b,
                    'actual_weight': actual,
                })
            self.env['curve.s.line'].create(lines)
            curve.plan_weight = plan
            curve.plan_weight_b = plan_b
            curve.actual_weight = actual
            curve.deviasi = actual - plan

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
    _description = 'S-Curve Line'
    
    curve_id = fields.Many2one('project.curve.s', string='S Curve', ondelete='cascade')
    date = fields.Date('Date')
    task_id = fields.Many2one('project.task', string='Task')
    project_id = fields.Many2one('project.project',string='Project')
    plan_weight = fields.Float(string='Plan Weight (%)')
    plan_weight_b = fields.Float(string='Plan B Weight (%)')
    actual_weight = fields.Float(string='Actual Weight (%)')