# -*- coding: utf-8 -*-
import math
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError, UserError

class BudgetPlan(models.Model):
    _name = 'budget.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Budget Plan'
    _rec_name = 'name'

    no_rab = fields.Char(string='No RAB', readonly=True, required=True, copy=False, default='New')
    name = fields.Char(string='Name', required=True)
    project = fields.Many2one('project.project', string='Project', required=True)
    customer = fields.Many2one('res.partner', string="Customer", required=True)
    boq = fields.Many2one('boq', string='BOQ', required=True, domain="[('status', '=', 'confirm')]")
    unit_price_data = fields.Many2one('unit.price.data', string="Unit Price Data", required=True, domain="[('status', '=', 'confirm')]")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    total_price = fields.Float(string='Total Price',  store=True, compute="_compute_totals")
    rab_mk_ids = fields.One2many('rab.mk', 'budget_plan_id', string='RAB MK')
    active = fields.Boolean(string="Active", default=True)

    # bagian pages info
    profit = fields.Float(string="Profit(%)", default=1.0)
    # tax = fields.Float(string="Tax(%)", default=1.0)

    # buat variabel penampung untuk profit biar ga ngubah cuy
    profit_material = fields.Float(string="Material", compute='_compute_profit')
    profit_wages = fields.Float(string="Wages", compute='_compute_profit')
    profit_equipment = fields.Float(string="Equipment", compute='_compute_profit')
    profit_total = fields.Float(string="Material", compute='_compute_profit')
    selisih_profit_material = fields.Float(string="Material", compute='_compute_profit')
    selisih_profit_wages = fields.Float(string="Wages", compute='_compute_profit')
    selisih_profit_equipment = fields.Float(string="Equipment", compute='_compute_profit')
    selisih_profit_total = fields.Float(string="Total", compute='_compute_profit')

    # buat variabel penampung untuk tax juga biar ga ngubah cuy cakeps *puyeng pala css report print
    tax_material = fields.Float(string="Material", compute='_compute_tax')
    tax_wages = fields.Float(string="Wages", compute='_compute_tax')
    tax_equipment = fields.Float(string="Equipment", compute='_compute_tax')
    tax_total = fields.Float(string="Total", compute='_compute_tax')
    selisih_tax_material = fields.Float(string="Material", compute='_compute_tax')
    selisih_tax_wages = fields.Float(string="Wages", compute='_compute_tax')
    selisih_tax_equipment = fields.Float(string="Equipment", compute='_compute_tax')
    selisih_tax_total = fields.Float(string="Total", compute='_compute_tax')

    # done untuk pembulatan
    sum_material = fields.Float(string="Sum Material", store=True, compute='_compute_rounded', inverse='_inverse_sum_material')
    sum_wages = fields.Float(string="Sum Wages", store=True, compute='_compute_rounded', inverse='_inverse_sum_wages')
    sum_equipment = fields.Float(string="Sum Equipment", store=True, compute='_compute_rounded', inverse='_inverse_sum_equipment')
    sum_total = fields.Float(string="Sum Total", compute="_compute_sum_total", store=True, readonly=True)

    #Calculation Tab
    total_material = fields.Float(string="Total Material",  store=True, compute="_compute_totals")
    total_wages = fields.Float(string="Total Wages",  store=True, compute="_compute_totals")
    total_equipment = fields.Float(string="Total Equipment",  store=True, compute="_compute_totals")
    total_tax_material = fields.Float(string="Tax Material", store=True)
    total_tax_wages = fields.Float(string="Tax Wages", store=True)
    total_tax_equipment = fields.Float(string="Tax Equipment", store=True)

    # untuk profit & tax
    @api.depends('profit', 'total_material', 'total_wages', 'total_equipment')
    def _compute_profit(self):
        for record in self:
            profit = record.profit if record.profit is not None else 0
            record.profit_material = (profit * record.total_material) / 100
            record.profit_wages = (profit * record.total_wages) / 100
            record.profit_equipment = (profit * record.total_equipment) / 100
            record.profit_total = record.profit_material + record.profit_wages + record.profit_equipment
            record.selisih_profit_material = record.total_material + record.profit_material
            record.selisih_profit_wages = record.total_wages + record.profit_wages
            record.selisih_profit_equipment = record.total_equipment + record.profit_equipment
            record.selisih_profit_total = record.selisih_profit_material + record.selisih_profit_wages + record.selisih_profit_equipment

    @api.depends('selisih_profit_material', 'selisih_profit_wages', 'selisih_profit_equipment')
    def _compute_tax(self):
        for record in self:
            record.selisih_tax_material = record.selisih_profit_material + record.total_tax_material
            record.selisih_tax_wages = record.selisih_profit_wages + record.total_tax_wages
            record.selisih_tax_equipment = record.selisih_profit_equipment + record.total_tax_equipment
            record.selisih_tax_total = record.selisih_tax_material + record.selisih_tax_wages + record.selisih_tax_equipment

    # # untuk pembulatan
    # @api.depends('selisih_tax_material', 'selisih_tax_wages', 'selisih_tax_equipment')
    def _compute_rounded(self):
        for record in self:
            record.sum_material = record._round_up(record.selisih_tax_material)
            record.sum_wages = record._round_up(record.selisih_tax_wages)
            record.sum_equipment = record._round_up(record.selisih_tax_equipment)

    def _round_up(self, value):
        if value:
            str_value = str(int(value))
            
            last_three_digits = int(str_value[-3:])
            
            if last_three_digits == 0:
                return value
            
            first_part = int(str_value[:-3]) if len(str_value) > 3 else 0
            
            if last_three_digits % 100 == 0:
                rounded_value = first_part * 1000 + last_three_digits
            else:
                rounded_value = first_part * 1000 + ((last_three_digits // 100) + 1) * 100
        
            return rounded_value
        
        return 0

    @api.depends('sum_material', 'sum_wages', 'sum_equipment')
    def _compute_sum_total(self):
        for record in self:
            # Hitung total berdasarkan material, wages, dan equipment yang bisa diubah manual
            record.sum_total = (record.sum_material or 0) + (record.sum_wages or 0) + (record.sum_equipment or 0)
        
    def _inverse_sum_material(self):
        for record in self:
            if record.sum_material is not None:
                record.sum_material = record.sum_material

    def _inverse_sum_wages(self):
        
        for record in self:
            if record.sum_wages is not None:
                record.sum_wages = record.sum_wages

    def _inverse_sum_equipment(self):
        for record in self:
            if record.sum_equipment is not None:
                record.sum_equipment = record.sum_equipment

    sale_order_ids = fields.Many2many('sale.order', string="Sale Orders")
    sale_order_count = fields.Integer(string='Sale Order', compute='_compute_sale_order_count')

    def _compute_sale_order_count(self):
        for rab in self:
            rab.sale_order_count = self.env['sale.order'].search_count([('rab_id', '=', rab.id)])

    def write(self, vals):
        if 'status' in vals:
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(BudgetPlan, self).write(vals)
    
    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'name': 'Sale Order',
            'domain': [('rab_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'context': {'default_rab_id': self.id, 'default_project':self.project.id},
        }

    def action_refresh(self):
        for record in self:
            record.rab_mk_ids = [(5, 0, 0)]
            record._depends_boq()
            record.rab_mk_ids._compute_volume_and_uom()
            record.rab_mk_ids._depends_unit_price()
            record.rab_mk_ids._compute_price()
            record.rab_mk_ids._compute_total_price()
            record.rab_mk_ids._compute_taxes_id()
            record.action_calculate()
    
    def action_calculate(self):
        for record in self:
            record._compute_total_taxes()
            record._compute_rounded()

    def action_sales_order(self):
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']

        for record in self:
            sale_order = sale_order_obj.create({
                'partner_id': record.customer.id,
                'project': record.project.id,
                'rab_id': record.id
            })

            wbs_dict = {}

            for rab_mk in record.rab_mk_ids:
                rab_mk._compute_price()
                
                if rab_mk.display_type:
                    sale_order_line_obj.create({
                        'order_id': sale_order.id,
                        'name': rab_mk.name,
                        'display_type': rab_mk.display_type,
                        'sequence': rab_mk.sequence,
                    })
                else:
                    product_template = rab_mk.wbs
                    if product_template:
                        if product_template.id in wbs_dict:
                            wbs_dict[product_template.id]['price_unit'] += rab_mk.price
                        else:
                            wbs_dict[product_template.id] = {
                                'product_id': product_template.wbs.name.product_variant_id.id,
                                'name': rab_mk.name,
                                'product_uom_qty': rab_mk.volume,
                                'price_unit': rab_mk.price,
                                'product_uom': product_template.wbs.name.uom_id.id,
                                'wbs_category': product_template.wbs_category.id,
                                'tax_id': [(6, 0, rab_mk.taxes_id.ids)],
                                'sequence': rab_mk.sequence
                            }

            for wbs_data in wbs_dict.values():
                sale_order_line_obj.create({
                    'order_id': sale_order.id,
                    'product_id': wbs_data['product_id'],
                    'name': wbs_data['name'],
                    'product_uom_qty': wbs_data['product_uom_qty'],
                    'price_unit': wbs_data['price_unit'],
                    'product_uom': wbs_data['product_uom'],
                    'wbs_category': wbs_data['wbs_category'],
                    'tax_id': wbs_data['tax_id'],
                    'sequence': wbs_data['sequence']
                })

            record.sale_order_ids = [(4, sale_order.id)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        if vals.get('no_rab', 'New') == 'New':
            vals['no_rab'] = self.env['ir.sequence'].next_by_code('no.rab') or 'New'
        result = super(BudgetPlan, self).create(vals)
        return result

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body="Confirmed by %s" % (self.env.user.name))

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body="Cancelled by %s" % (self.env.user.name))

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body="Set to Draft by %s" % (self.env.user.name))

    def _depends_boq(self):
        for record in self:
            if record.boq:
                boq_record = record.boq.boq_mk_ids
                wbs = []

                for x in boq_record:
                    if x.ahs:
                        wbs.append((0, 0, {
                            'wbs' : x.ahs.id,
                            'name' : x.ahs.display_name
                        }))
                record.rab_mk_ids = wbs
            else:
                record.rab_mk_ids = [(5, 0, 0)]
    
    @api.depends('rab_mk_ids.material', 'rab_mk_ids.wages', 'rab_mk_ids.equipment', 'rab_mk_ids.volume')
    def _compute_totals(self):
        for record in self:
            total_material = 0.0
            total_wages = 0.0
            total_equipment = 0.0

            for line in record.rab_mk_ids:
                
                total_material += line.material * line.volume
                total_wages += line.wages * line.volume
                total_equipment += line.equipment * line.volume

            record.total_material = total_material
            record.total_wages = total_wages
            record.total_equipment = total_equipment
            record.total_price = total_material + total_wages + total_equipment
    
    def _compute_total_taxes(self):
        for record in self:
            total_tax_material = 0.0
            total_tax_wages = 0.0
            total_tax_equipment = 0.0
            
            for line in record.rab_mk_ids:
                line_total_material = line.material * line.volume
                line_total_wages = line.wages * line.volume
                line_total_equipment = line.equipment * line.volume

                if line.taxes_id:
                    tax = line.taxes_id.compute_all(line_total_material)['taxes'][0]['amount']
                    total_tax_material += tax
                    tax = line.taxes_id.compute_all(line_total_wages)['taxes'][0]['amount']
                    total_tax_wages += tax
                    tax = line.taxes_id.compute_all(line_total_equipment)['taxes'][0]['amount']
                    total_tax_equipment += tax

            record.total_tax_material = total_tax_material
            record.total_tax_wages = total_tax_wages
            record.total_tax_equipment = total_tax_equipment

class RabMK(models.Model):
    _name = 'rab.mk'
    _description = 'RAB'

    budget_plan_id = fields.Many2one('budget.plan', string='Budget Plan')
    wbs = fields.Many2one('unit.price.analysis', string="WBS")
    volume = fields.Float(string='Volume', digits=(16, 3))
    uom = fields.Many2one('uom.uom', string='UOM')
    material = fields.Float('Material', store=True)
    wages = fields.Float('Wages', store=True)
    equipment = fields.Float('Equipment', store=True)
    price = fields.Float(string='Price', compute='_compute_price', store=True)
    subtotal_price = fields.Float(string='Subtotal Price', compute='_compute_total_price', store=True)
    taxes_id = fields.Many2one('account.tax', string='Taxes')
    taxed = fields.Float(compute='_compute_taxed', store=True)

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description')    
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    
    @api.model
    def create(self, vals):
        if 'sequence' not in vals:
            vals['sequence'] = self.env['rab.mk'].search([], order='sequence desc', limit=1).sequence + 10
        if vals.get('display_type'):
            vals.update(wbs=False)
        return super(RabMK, self).create(vals)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError("You cannot change the type of a warranty order line. Instead you should delete the current line and create a new line of the proper type.")
        
        if 'sequence' in values:
            new_sequence = values['sequence']
            
            existing_sequence = self.mapped('sequence')
            if new_sequence in existing_sequence:
                raise UserError("This sequence value already exists. Please choose a unique sequence value.")
            
            values['sequence'] = new_sequence

        return super(RabMK, self).write(values)

    _sql_constraints = [
        ('accountable_required_fields',
            "CHECK(display_type IS NOT NULL OR (product_id IS NOT NULL AND quantity IS NOT NULL))",
            "Missing required fields on accountable warranty request line."),
        ('non_accountable_null_fields',
            "CHECK(display_type IS NULL OR (product_id IS NULL AND quantity = 0))",
            "Forbidden values on non-accountable warranty request line"),]

    def _compute_volume_and_uom(self):
        for record in self:
            if record.wbs and record.budget_plan_id.boq:

                boq_mks_ids = record.budget_plan_id.boq.boq_mk_ids.filtered(lambda a: a.ahs == record.wbs)

                for i in boq_mks_ids:
                    record.volume = i.volume
                    record.uom = i.uom.id
            else:
                record.volume = 0
                record.uom = False

    def _depends_unit_price(self):
        for record in self:
            material_total = 0.0
            wages_total = 0.0
            equipment_total = 0.0

            materials = self.env['ahs.material'].search([
                ('unit_price_analysis_id', '=', record.wbs.id)
            ])
            for material in materials:
                price_material = self.env['price.material'].search([
                    ('unit_price_data_id', '=', record.budget_plan_id.unit_price_data.id),
                    ('material', '=', material.product.id)
                ], limit=1)
                if price_material:
                    material_total += material.koefisien * price_material.unit_price

            wages = self.env['ahs.wages'].search([
                ('unit_price_analysis_id', '=', record.wbs.id)
            ])
            for wage in wages:
                price_wages = self.env['price.wages'].search([
                    ('unit_price_data_id', '=', record.budget_plan_id.unit_price_data.id),
                    ('work_item', '=', wage.product.id)
                ], limit=1)
                if price_wages:
                    wages_total += wage.koefisien * price_wages.wages

            equipments = self.env['ahs.equipment'].search([
                ('unit_price_analysis_id', '=', record.wbs.id)
            ])
            for equipment in equipments:
                price_equipment = self.env['price.equipment'].search([
                    ('unit_price_data_id', '=', record.budget_plan_id.unit_price_data.id),
                    ('equipment', '=', equipment.product.id)
                ], limit=1)
                if price_equipment:
                    equipment_total += equipment.koefisien * price_equipment.unit_price

            record.material = material_total
            record.wages = wages_total
            record.equipment = equipment_total

    def _compute_price(self):
        for record in self:
            record.price = (record.material + record.wages + record.equipment)

    def _compute_total_price(self):
        for record in self:
            record.subtotal_price = (record.material + record.wages + record.equipment) * record.volume

    def _compute_taxes_id(self):
        for record in self:
            record.taxes_id = record.wbs.wbs.name.taxes_id if record.wbs else None

    @api.depends('taxes_id')
    def _compute_taxed(self):
        for record in self:
            if record.taxes_id:
                tax_percent = record.taxes_id.amount / 100.0
                record.taxed = record.subtotal_price * (1 + tax_percent)
            else:
                record.taxed = record.subtotal_price
