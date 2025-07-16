from odoo import models, fields, api, _, exceptions
from odoo.exceptions import ValidationError

class NonConformanceReportForm(models.Model):
    _name = 'nonconformance.report.form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Non-Conformance Report Form'
    _rec_name = 'no_ncrf'

    no_ncrf = fields.Char(string="No Non-Conformance Report Form", readonly=True, required=True, copy=False, default='New')
    submission_date = fields.Date('Submission Date')
    contract_number = fields.Char('Contract Number')
    contract_date = fields.Date('Contract Date')
    package_name = fields.Char('Package Name')
    contruction_provider = fields.Many2one('res.partner', string='Construction Service Provider')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    active = fields.Boolean(string="Active", default=True)

    # Data Details
    project = fields.Many2one('project.project', string='Project', required=True)
    work_activities = fields.Text(string='Work Activities')
    work_location = fields.Char(string='Work Location')
    info = fields.Char(string='More Info')

    # Description
    actual_condition = fields.Text(string='Actual Conditions')
    condition = fields.Text(string='Conditions')

    # Plan
    proposal_plan = fields.Selection([
        ('fixed', 'Fixed'),
        ('dismantle', 'Dismantle and Rework'),
        ('acceptable', 'Acceptable with a Note')
    ], string='Proposed Follow-up Plan')
    other = fields.Char(string='Other')
    followup_desc = fields.Text(string='Follow-up Description')

    # Measures
    proposal_measures = fields.Text(string='Proposed Preventive Measures')

    @api.model
    def create(self, vals):
        if vals.get('no_ncrf', 'New') == 'New':
            vals['no_ncrf'] = self.env['ir.sequence'].next_by_code('no.ncrf') or 'New'
        result = super(NonConformanceReportForm, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(NonConformanceReportForm, self).write(vals)
    
    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")

    @api.constrains('proposal_plan', 'other')
    def _check_proposal_plan_and_other(self):
        for record in self:
            if not record.proposal_plan and not record.other:
                raise ValidationError("Please fill in either 'Proposed Follow-up Plan' or 'Other'.")