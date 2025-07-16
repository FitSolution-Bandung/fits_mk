import io
import base64
from odoo import models, fields, api, _, exceptions

class StakeholderAnalysis(models.Model):
    _name = 'stakeholder.analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Stakeholder Analysis'
    _rec_name = 'name_analysis'

    no_stakeholder = fields.Char(string="No Stakeholder", readonly=True, required=True, copy=False, default='New')
    name_analysis = fields.Char(string='Project Name', required=True)
    active = fields.Boolean(string="Active", default=True)

    # eksplorasi button import excel
    excel_file = fields.Binary(string="Download File")
    excel_file_name = fields.Char(string="File Name")
    
    @api.model
    def create(self, vals):
        if vals.get('no_stakeholder', 'New') == 'New':
            vals['no_stakeholder'] = self.env['ir.sequence'].next_by_code('no.stakeholder') or 'New'
        result = super(StakeholderAnalysis, self).create(vals)
        return result

    # data status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    # data page analysis risk mitigation details
    stakeholder_analysis_ids = fields.One2many('stakeholder.analysis.detail', 'analysis_id', string="Stakeholder Analysis Details")

    def write(self, vals):
        if 'status' in vals:
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(StakeholderAnalysis, self).write(vals)
    
    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")

    # def action_export_to_excel(self):
    #     """Generate Excel file for Risk Mitigation data."""
    #     output = io.BytesIO()

    #     # Menggunakan xlsxwriter untuk membuat file Excel
    #     import xlsxwriter
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     worksheet = workbook.add_worksheet("Stakeholder Analysis")

    #     # Header
    #     headers = ['No', 'Name', 'Contact Person', 'Impact', 'Influence', 'Important', 'Contribute', 'Block the Project', 'Enganging the Stakeholder', 'Description']
    #     for col, header in enumerate(headers):
    #         worksheet.write(0, col, header)

    #     # Data rows
    #     row = 1
    #     for sh in self.stakeholder_analysis_ids:
    #         worksheet.write(row, 0, row)
    #         worksheet.write(row, 1, sh.name.display_name or '')
    #         worksheet.write(row, 2, sh.cp or '')
    #         worksheet.write(row, 3, sh.impact or '')
    #         worksheet.write(row, 4, sh.influence or '')
    #         worksheet.write(row, 5, sh.important or '')
    #         worksheet.write(row, 6, sh.contribute or '')
    #         worksheet.write(row, 7, sh.block_project or '')
    #         worksheet.write(row, 8, sh.engaging or '')
    #         worksheet.write(row, 9, sh.description or '')
    #         row += 1

    #     workbook.close()

    #     # Mengonversi file ke Base64 untuk diunduh
    #     file_data = base64.b64encode(output.getvalue())
    #     output.close()

    #     self.write({
    #         'excel_file': file_data,
    #         'excel_file_name': f"Stakeholder_{self.name_analysis}.xlsx",
    #     })

    #     return {
    #     'type': 'ir.actions.act_url',
    #     'url': f'/download/stakeholder_analysis_excel/{self.id}',
    #     'target': 'self',
    # }

class StakeholderAnalysisDetail(models.Model):
    _name = 'stakeholder.analysis.detail'
    _rec_name = 'name'

    name            = fields.Many2one('res.partner', string='Stakeholder', required=True)
    cp              = fields.Text(string="Contact Person")
    impact          = fields.Selection([
                            ('low', 'Low'),
                            ('high', 'High')
                        ], string='Impact')
    influence       = fields.Selection([
                            ('low', 'Low'),
                            ('high', 'High')
                        ], string='Influence')
    important       = fields.Char(string="Important", compute='_compute_important', readonly=True)
    contribute      = fields.Char(string="Contribute")
    block_project   = fields.Char(string="Block the Project")
    engaging        = fields.Char(string="Engaging the Stakeholder")
    description     = fields.Char(string="Description")
    analysis_id = fields.Many2one('stakeholder.analysis', string="Stakeholder Analysis")

    @api.depends('impact', 'influence')
    def _compute_important(self):
        for rec in self:
            if rec.impact == 'high' and rec.influence == 'high':
                rec.important = 'Key Player - Engaged Closely'
            elif rec.impact == 'high' and rec.influence == 'low':
                rec.important = 'Meet their needs - Keep Satisfied'
            elif rec.impact == 'low' and rec.influence == 'high':
                rec.important = 'Show consideration - Keep Informed'
            elif rec.impact == 'low' and rec.influence == 'low':
                rec.important = 'Least important - Minimal effort'
            else:
                rec.important = ''