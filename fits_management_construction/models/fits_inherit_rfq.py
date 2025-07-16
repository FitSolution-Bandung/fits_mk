from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    boq_id = fields.Many2one('boq', string='BOQ')
    boq_count = fields.Integer(string='BoQ Count', compute='_compute_boq_count')

    def _compute_boq_count(self):
        for po in self:
            po.boq_count = self.env['boq'].search_count([('id', '=', po.boq_id.id)])

    def action_view_boq(self):
        self.ensure_one()
        return {
            'name': 'Bill Of Quantity',
            'domain': [('id', '=', self.boq_id.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'boq',
            'type': 'ir.actions.act_window',
            'context': {'default_boq_ids': self.boq_id.id},
        }