# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project = fields.Many2one('project.project', string='Project')

    rab_id = fields.Many2one('budget.plan', string='Budget Plan')
    rab_count = fields.Integer(string='Sale Order', compute='_compute_rab_count')

    def _compute_rab_count(self):
        for so in self:
            so.rab_count = self.env['budget.plan'].search_count([('sale_order_ids', '=', so.id)])

    def action_view_budget_plan(self):
        self.ensure_one()
        return {
            'name': 'Budget Plan',
            'domain': [('sale_order_ids', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'budget.plan',
            'type': 'ir.actions.act_window',
            'context': {'default_sale_order_ids':self.id},
        }
    
    def action_confirm(self):
        """ Override method action_confirm untuk mengubah project assignment """
        super(SaleOrder, self).action_confirm()

        # total_cost = 0

        for line in self.order_line:
            if line.product_id.type == 'service' and line.is_service and line.task_id:
                if self.project:
                    line.task_id.project_id = self.project
                    line.product_id.project_id = self.project    
                    line.task_id.name = line.product_id.name
                    line.task_id.wbs_category = line.wbs_category
                    line.task_id.task_cost = line.price_subtotal
                    
                    # total_cost += line.price_total

        if self.project:
            self.project.total_cost = self.amount_untaxed

        return True

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    wbs_category = fields.Many2one('wbs.category', string="WBS Category")