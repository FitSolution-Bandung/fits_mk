# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_rab = fields.Boolean(string='Is RAB/WBS Product', default=False)
    rab_category = fields.Selection([
        ('material', 'Material'),
        ('wages', 'Wages'),
        ('equipment', 'Equipment')
    ], string='RAB Category', default='')

    unit_price_analysis_count = fields.Integer(string='Unit Price Analysis Count', compute='_compute_unit_price_analysis_count')

    def _compute_unit_price_analysis_count(self):
        for product in self:
            product.unit_price_analysis_count = self.env['unit.price.analysis'].search_count([
                '|', '|',
                ('ahs_material_ids.product', '=', product.id),
                ('ahs_wages_ids.product', '=', product.id),
                ('ahs_equipment_ids.product', '=', product.id),
                ('status', '=', 'confirm')
            ])

    def action_view_unit_price_analysis(self):
        self.ensure_one()
        return {
            'name': 'Unit Price Analysis',
            'domain': [
                '|', '|',
                ('ahs_material_ids.product', '=', self.id),
                ('ahs_wages_ids.product', '=', self.id),
                ('ahs_equipment_ids.product', '=', self.id),
                ('status', '=', 'confirm')
            ],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'unit.price.analysis',
            'type': 'ir.actions.act_window',
            'context': {'default_product': self.id},
        }
    
    wbs_count = fields.Integer(string='WBS Count', compute='_compute_wbs_count')

    def _compute_wbs_count(self):
        for product in self:
            product.wbs_count = self.env['wbs'].search_count([
                ('name', '=', product.id),
            ])

    def action_view_wbs(self):
        self.ensure_one()
        return {
            'name': 'WBS',
            'domain': [
                ('name', '=', self.id),
            ],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'wbs',
            'type': 'ir.actions.act_window',
            'context': {'default_product': self.id},
        }