# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class AttendancesTemplate(models.Model):
    _inherit = 'hr.attendance'

    job_position = fields.Char(related='employee_id.job_title', string='Job Position', readonly=True)
    project_name = fields.Many2one('project.project', string='Project')

class BackDateAttendance(models.Model):
    _name = 'back.date.attendance'

    employee = fields.Many2one('hr.employee', string='Employee')
    check_in = fields.Datetime('Check In')
    check_out = fields.Datetime('Check Out')
    project = fields.Many2one('project.project', string='Project')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', default='draft')

    def action_confirm(self):
        self.status = 'confirm'

        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': self.check_in,
            'check_out': self.check_out,
            'project_name': self.project.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Attendance Overview'),
            'res_model': 'hr.attendance',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('check_in', '>=', self.check_in), ('check_out', '<=', self.check_out)],
        }

    def action_draft(self):
        self.status = 'draft'

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for record in self:
            if isinstance(record.check_in, datetime) and isinstance(record.check_out, datetime):
                if record.check_out < record.check_in:
                    raise ValidationError("Check-out time cannot be earlier than check-in time")
            else:
                raise ValidationError("Invalid datetime format")