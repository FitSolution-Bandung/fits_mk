# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class UnitPriceData(models.Model):
    _name = 'unit.price.data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Unit Price Data'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    no_upd = fields.Char(string='No Unit Price Data', readonly=True, required=True, copy=False, default='New')
    province = fields.Many2one('res.country.state', string='Province', required=True, domain="[('country_id', '=', 'Indonesia')]")
    location = fields.Many2one('location', string='Location', required=True, domain="[('province', '=', province)]")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    price_material_ids = fields.One2many('price.material', 'unit_price_data_id', string='Price Material')
    price_wages_ids = fields.One2many('price.wages', 'unit_price_data_id', string='Price Wages')
    price_equipment_ids = fields.One2many('price.equipment', 'unit_price_data_id', string='Price Equipment')
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals):
        if vals.get('no_upd', 'New') == 'New':
            vals['no_upd'] = self.env['ir.sequence'].next_by_code('no.upd') or 'New'
        result = super(UnitPriceData, self).create(vals)
        return result
    
    def write(self, vals):
        if 'status' in vals:
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(UnitPriceData, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body="Confirmed by %s" % (self.env.user.name))

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body="Cancelled by %s" % (self.env.user.name))

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body="Set to Draft by %s" % (self.env.user.name))

    budget_plan_count = fields.Integer(string='Budget Plan Count', compute='_compute_budget_plan_count')

    def _compute_budget_plan_count(self):
        for x in self:
            x.budget_plan_count = self.env['budget.plan'].search_count([
                ('unit_price_data', '=', x.id),
                ('status', '=', 'confirm')
            ])

    def action_view_budget_plan(self):
        self.ensure_one()
        return {
            'name': 'Budget Plan',
            'domain': [
                ('unit_price_data', '=', self.id),
                ('status', '=', 'confirm')
            ],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'budget.plan',
            'type': 'ir.actions.act_window',
            'context': {'default_unit_price_data': self.id},
        }

class PriceMaterial(models.Model):
    _name = 'price.material'
    _description = 'Price Material'

    unit_price_data_id = fields.Many2one('unit.price.data', string='Unit Price Data')
    material = fields.Many2one('product.template', string='Material', domain="[('rab_category', '=', 'material'), ('rab_category', '!=', False)]")
    uom = fields.Many2one('uom.uom', string='Unit Of Measure')
    unit_price = fields.Float(string='Unit Price')

    @api.onchange('material')
    def _onchange_material(self):
        if self.material:
            self.uom = self.material.uom_id
            self.unit_price = self.material.standard_price
            return
        else:
            self.uom = False
            self.unit_price = 0

class PriceWages(models.Model):
    _name = 'price.wages'
    _description = 'Price Wages'

    unit_price_data_id = fields.Many2one('unit.price.data', string='Unit Price Data')
    work_item = fields.Many2one('product.template', string='Work Item', domain="[('rab_category', '=', 'wages'), ('rab_category', '!=', False)]")
    uom = fields.Many2one('uom.uom', string='Unit Of Measure')
    wages = fields.Float(string='Wages')

    @api.onchange('work_item')
    def _onchange_work_item(self):
        if self.work_item:
            self.uom = self.work_item.uom_id
            self.wages = self.work_item.standard_price
            return
        else:
            self.uom = False
            self.wages = 0

class PriceEquipment(models.Model):
    _name = 'price.equipment'
    _description = 'Price Equipment'

    unit_price_data_id = fields.Many2one('unit.price.data', string='Unit Price Data')
    equipment = fields.Many2one('product.template', string='Equipment', domain="[('rab_category', '=', 'equipment'), ('rab_category', '!=', False)]")
    uom = fields.Many2one('uom.uom', string='Unit Of Measure')
    unit_price = fields.Float(string='Unit Price')

    @api.onchange('equipment')
    def _onchange_equipment(self):
        if self.equipment:
            self.uom = self.equipment.uom_id
            self.unit_price = self.equipment.standard_price
            return
        else:
            self.uom = False
            self.unit_price = 0