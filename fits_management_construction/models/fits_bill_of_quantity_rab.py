# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError

class BillOfQuantity(models.Model):
    _name = 'boq'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Bill Of Quantity'
    _rec_name = 'name'

    no_boq = fields.Char(string='No Bill of Quantity', readonly=True, required=True, copy=False, default='New')
    name = fields.Char(string='Name', required=True)
    project = fields.Many2one('project.project', string='Project', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    boq_mk_ids = fields.One2many('boq.mk', 'boq_id', string='Bill Of Quantity')
    active = fields.Boolean(string="Active", default=True)
    rfq_ids = fields.One2many('purchase.order', 'boq_id', string="RFQ")
    rfq_count = fields.Integer(string="RFQ Count", compute="_compute_rfq_count")

    @api.model
    def create(self, vals):
        if vals.get('no_boq', 'New') == 'New':
            vals['no_boq'] = self.env['ir.sequence'].next_by_code('no.boq') or 'New'
        result = super(BillOfQuantity, self).create(vals)
        return result
    
    def write(self, vals):
        if 'status' in vals:
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(BillOfQuantity, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body="Confirmed by %s" % (self.env.user.name))

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body="Cancelled by %s" % (self.env.user.name))
        # perbaikan
        rfq = self.env['purchase.order'].search([('origin', '=', self.no_boq)], limit=1)
        
        if rfq:
            # Jika status RFQ adalah 'draft' atau 'sent', kita bisa batalkan
            if rfq.state in ['draft', 'sent']:
                rfq.button_cancel() 
                rfq.unlink()
                self.rfq_count = 0
            else:
                raise UserError("RFQ sudah tidak bisa dibatalkan karena statusnya bukan 'draft' atau 'sent'.")
        
        self.status = 'cancelled'

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body="Set to Draft by %s" % (self.env.user.name))
    
    def _compute_rfq_count(self):
        for rec in self:
            rec.rfq_count = self.env['purchase.order'].search_count([('boq_id', '=', rec.id)]) 

    def action_view_rfq(self):
        self.ensure_one()
        return {
            'name': _('RFQ'),
            'domain': [('boq_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'context': {'default_boq_id': self.id},
        }
    
    def action_rfq(self):

        if not self.vendor:
            raise UserError("Vendor belum ditentukan.")
        
        # Membuat objek RFQ (purchase.order)
        rfq_obj = self.env['purchase.order']
        
        # Persiapkan data untuk purchase.order
        rfq_data = {
            'partner_id': self.vendor.id,
            'origin': self.no_boq,
            'order_line': [],
            'boq_id' : self.id,
        }

        # Loop untuk setiap item dalam BOQ (boq_mk_ids) untuk membuat purchase.order.line
        for line in self.boq_mk_ids:
            if not line.ahs:
                raise UserError("Data AHS belum lengkap untuk item BOQ.")
            # if not line.ahs.wbs.name.standard_price:
            #     raise UserError("Cost tidak ditentukan pada produk WBS.")

            # Persiapkan data untuk tiap purchase.order.line
            line_data = {
                'product_id': line.ahs.wbs.name.product_variant_id.id,
                'name': line.ahs.wbs.name.product_variant_id.name,
                'product_qty': line.volume,
                'price_unit': line.ahs.wbs.name.standard_price,
                'date_planned': fields.Date.today(),
            }
            rfq_data['order_line'].append((0, 0, line_data))

        # Membuat purchase.order dengan line detailnya
        rfq = rfq_obj.create(rfq_data)
        self.message_post(body="RFQ created with ID: %s" % (rfq.name))

        # Mengarahkan pengguna ke RFQ yang baru dibuat
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request for Quotation',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': rfq.id,
            'target': 'current',
        }
    
    budget_plan_count = fields.Integer(string='Budget Plan Count', compute='_compute_budget_plan_count')

    def _compute_budget_plan_count(self):
        for x in self:
            x.budget_plan_count = self.env['budget.plan'].search_count([
                ('boq', '=', x.id),
                ('status', '=', 'confirm')
            ])

    def action_view_budget_plan(self):
        self.ensure_one()
        return {
            'name': 'Budget Plan',
            'domain': [
                ('boq', '=', self.id),
                ('status', '=', 'confirm')
            ],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'budget.plan',
            'type': 'ir.actions.act_window',
            'context': {'default_boq': self.id},
        }
           
class BoqMk(models.Model):
    _name = 'boq.mk'
    _description = 'RAB'

    boq_id = fields.Many2one('boq', string='BOQ')
    ahs = fields.Many2one('unit.price.analysis', string="AHS")
    calculation = fields.Text(string='Calculation', default="-")
    uom = fields.Many2one('uom.uom', string='UoM', compute='_get_uom')
    volume = fields.Float(string='Volume')
    attachment = fields.Binary(string='Attachment')
    
    @api.depends('ahs')
    def _get_uom(self):
        for record in self:
            if record.ahs and record.ahs.wbs.name:
                if record.ahs.wbs.name.uom_id:
                    record.uom = record.ahs.wbs.name.uom_id.id 
                else:
                    record.uom = False 
            else:
                record.uom = False 