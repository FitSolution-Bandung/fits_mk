from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sign = fields.Image(string="Sign", max_width=256, max_height=256)