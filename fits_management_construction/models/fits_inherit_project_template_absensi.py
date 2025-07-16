# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProjectTemplate(models.Model):
    _inherit = 'project.project'

    manpower_ids = fields.Many2many('hr.employee', string='Manpower')
    job_title = fields.Char(related='manpower_ids.job_title', string='Job Title', readonly=True)

# class ProjectTemplate(models.Model):
#     _inherit='project.project'

#     manpower_ids = fields.Many2many('project.manpower.detail', string='Manpower')

# class ProjectTemplateDetail(models.Model):
#     _name = 'project.manpower.detail'
#     _rec_name = 'name'
    
#     name = fields.Many2one('hr.employee', string='Manpower')
#     job_title = fields.Char(related='name.job_title', string='Job Title', readonly=True)

