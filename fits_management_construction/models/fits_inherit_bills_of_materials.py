from odoo import models, fields, api, _

class BomDescription(models.Model):
    _inherit = 'mrp.bom.line'

    description = fields.Char(string="Description")