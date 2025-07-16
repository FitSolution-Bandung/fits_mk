# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Stakeholder(models.Model):
    _inherit = 'res.partner'  # Menggunakan inherit dari res.partner

# class Stakeholder(models.Model):
#     _name = 'stakeholder'
#     _description = 'Stakeholder'
#     _rec_name = 'name'

#     name = fields.Many2one('res.partner', string="Stakeholder")
#     email = fields.Char(related='name.email', string="Email", store=True)
#     phone = fields.Char(related='name.phone', string="Phone", store=True)
#     company_type = fields.Selection(related='name.company_type', string="Company Type", store=True)
#     state_id = fields.Many2one('res.country.state', related='name.state_id', string="State", store=True)
#     city = fields.Char(related='name.city', string="City", store=True)
    
class FieldCondition(models.Model):
    _name = 'field.condition.type'
    _description = 'Field Condition Type'
    _rec_name = 'name'

    name = fields.Char(string="Field Condition")

class Likelihood(models.Model):
    _name = 'likelihood'
    _description = 'Likelihood'
    _rec_name = 'no'

    no = fields.Char(string="No")
    name = fields.Char(string="Likelihood")

class Impact(models.Model):
    _name = 'impact'
    _description = 'Impact'
    _rec_name = 'no'

    no = fields.Char(string="No")
    name = fields.Char(string="Impact")

class RiskScale(models.Model):
    _name = 'risk.scale'
    _description = 'Risk Scale'
    _rec_name = 'name'

    name = fields.Char(string="Risk Scale", required=True)
    scale_from = fields.Integer(string="Scale From")
    scale_to = fields.Integer(string="Scale To")
    description = fields.Text(string="Description")

class RiskMitigationType(models.Model):
    _name = 'risk.mitigation.type'
    _description = 'Risk Mitigation Type'
    _rec_name = 'name'

    name = fields.Char(string="Risk Mitigation")
    description = fields.Text(string="Description")

class GeneralDanger(models.Model):
    _name = 'general.danger'
    _description = 'General Danger'
    _rec_name = 'name'

    name = fields.Char(string="General Danger")

class Location(models.Model):
    _name = 'location'
    _description = 'Location'
    _rec_name = 'states'

    province = fields.Many2one('res.country.state', string="Province", domain="[('country_id', '=', 'Indonesia')]")
    states   = fields.Char(string="State")
    code     = fields.Char(string="Code") 

    # def create_location_data(self):
    #     state_vals = [
    #         {'states': 'Aceh', 'province': 613},
    #         {'states': 'Denpasar', 'province': 614},
    #     ]
    #     for val in state_vals:
    #         self.create(val)

class UnitCategory(models.Model):
    _name = 'unit.category'
    _description = 'Unit Category'
    _rec_name = 'name'

    name = fields.Char(string="Unit Category")

class BuildingCategory(models.Model):
    _name = 'building.category'
    _description = 'Building Category'
    _rec_name = 'name'

    name = fields.Char(string="Name")

class UomMK(models.Model):
    _inherit = 'uom.category'

    @api.model
    def toggle_menu_item_visibility(self):
        # Membaca status checkbox group_uom
        is_enabled = self.env['ir.config_parameter'].sudo().get_param('uom.group_uom', default=False)

        try:
            # Menemukan menu item berdasarkan external ID
            menu = self.env.ref('fts_management_construction.menu_uom_category')  # Ganti 'module_name' dengan nama modul Anda

            # Mengubah status aktif menu
            menu.sudo().write({'active': is_enabled})
        except ValueError:
            # Jika menu tidak ditemukan
            pass


class WBSCategory(models.Model):
    _name = 'wbs.category'
    _description = 'WBS Category'
    _rec_name = 'wbs_category'

    code = fields.Char(string="Code")
    wbs_category = fields.Char(string="WBS Category")
    wbs_ids = fields.One2many('wbs', 'wbs_category', string="WBS")

    unit_price_analysis_count = fields.Integer(string='Unit Price Analysis Count', compute='_compute_unit_price_analysis_count')

    def _compute_unit_price_analysis_count(self):
        for x in self:
            x.unit_price_analysis_count = self.env['unit.price.analysis'].search_count([
                ('wbs_category', '=', x.id),
                ('status', '=', 'confirm')
            ])

    def action_view_unit_price_analysis(self):
        self.ensure_one()
        return {
            'name': 'Unit Price Analysis',
            'domain': [
                ('wbs_category', '=', self.id),
                ('status', '=', 'confirm')
            ],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'unit.price.analysis',
            'type': 'ir.actions.act_window',
            'context': {'default_wbs_category': self.id},
        }
    
class WBS(models.Model):
    _name = 'wbs'
    _description = 'WBS'
    _rec_name = 'name'

    number = fields.Char(string="Number")
    name = fields.Many2one('product.template', string="Name", domain="[('is_rab', '=', 'True'), ('detailed_type', '=', 'service')]")
    level = fields.Selection([('2', '2'), ('3', '3'), ('4', '4')], string="Level")
    wbs_category = fields.Many2one('wbs.category', string="WBS Category", ondelete='cascade')

    unit_price_analysis_count = fields.Integer(string='Unit Price Analysis Count', compute='_compute_unit_price_analysis_count')

    def _compute_unit_price_analysis_count(self):
        for x in self:
            x.unit_price_analysis_count = self.env['unit.price.analysis'].search_count([
                ('wbs', '=', x.id),
                ('status', '=', 'confirm')
            ])

    def action_view_unit_price_analysis(self):
        self.ensure_one()
        return {
            'name': 'Unit Price Analysis',
            'domain': [
                ('wbs', '=', self.id),
                ('status', '=', 'confirm')
            ],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'unit.price.analysis',
            'type': 'ir.actions.act_window',
            'context': {'default_wbs': self.id},
        }