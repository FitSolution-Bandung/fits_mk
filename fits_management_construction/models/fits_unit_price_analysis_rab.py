# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class UnitPriceAnalysis(models.Model):
    _name = 'unit.price.analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Unit Price Analysis'
    _rec_name = 'wbs'

    no_ahs = fields.Char(string='No AHS', readonly=True, required=True, copy=False, default='New')
    name = fields.Char(string='Name', required=True)
    wbs_category = fields.Many2one('wbs.category', string='WBS Category', store=True)
    wbs = fields.Many2one('wbs', string='WBS', domain="[('wbs_category', '=', wbs_category)]")
    code = fields.Char('Code')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    ahs_material_ids = fields.One2many('ahs.material', 'unit_price_analysis_id', string='AHS Material')
    ahs_wages_ids = fields.One2many('ahs.wages', 'unit_price_analysis_id', string='AHS Wages')
    ahs_equipment_ids = fields.One2many('ahs.equipment', 'unit_price_analysis_id', string='AHS Equipment')
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals):
        if vals.get('no_ahs', 'New') == 'New':
            vals['no_ahs'] = self.env['ir.sequence'].next_by_code('no.ahs') or 'New'
        result = super(UnitPriceAnalysis, self).create(vals)
        return result
    
    def write(self, vals):
        if 'status' in vals:
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(UnitPriceAnalysis, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body="Confirmed by %s" % (self.env.user.name))

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body="Cancelled by %s" % (self.env.user.name))

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body="Set to Draft by %s" % (self.env.user.name))

    boq_count = fields.Integer(string='Budget Plan Count', compute='_compute_boq_count')

    def _compute_boq_count(self):
        for x in self:
            x.boq_count = self.env['boq'].search_count([
                ('boq_mk_ids.ahs', '=', x.id),
                ('status', '=', 'confirm')
            ])

    def action_view_boq(self):
        self.ensure_one()
        return {
            'name': 'Budget Plan',
            'domain': [
                ('boq_mk_ids.ahs', '=', self.id),
                ('status', '=', 'confirm')
            ],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'boq',
            'type': 'ir.actions.act_window',
            'context': {'default_boq_mk_ids.ahs': self.id},
        }

class AhsMaterial(models.Model):
    _name = 'ahs.material'
    _description = 'AHS Material'

    unit_price_analysis_id = fields.Many2one('unit.price.analysis', string='Unit Price Analysis')
    product = fields.Many2one('product.template', string='Product', domain="[('rab_category', '!=', False), ('rab_category', '=', 'material')]")
    koefisien = fields.Float(string='Koefesien', digits=(16, 3))
    uom = fields.Many2one('uom.uom', string='UoM')

    @api.onchange('product')
    def _onchange_product(self):
        if self.product:
            self.uom = self.product.uom_id.id
            return
        
class AhsWages(models.Model):
    _name = 'ahs.wages'
    _description = 'AHS Wages'

    unit_price_analysis_id = fields.Many2one('unit.price.analysis', string='Unit Price Analysis')
    product = fields.Many2one('product.template', string='Product', domain="[('rab_category', '!=', False), ('rab_category', '=', 'wages')]")
    koefisien = fields.Float(string='Koefesien', digits=(16, 3))
    uom = fields.Many2one('uom.uom', string='UoM')

    @api.onchange('product')
    def _onchange_product(self):
        if self.product:
            self.uom = self.product.uom_id.id
            return

class AhsEquipment(models.Model):
    _name = 'ahs.equipment'
    _description = 'AHS Equipment'

    unit_price_analysis_id = fields.Many2one('unit.price.analysis', string='Unit Price Analysis')
    product = fields.Many2one('product.template', string='Product', domain="[('rab_category', '!=', False), ('rab_category', '=', 'equipment')]")
    koefisien = fields.Float(string='Koefesien', digits=(16, 3))
    uom = fields.Many2one('uom.uom', string='UoM')

    @api.onchange('product')
    def _onchange_product(self):
        if self.product:
            self.uom = self.product.uom_id.id
            return