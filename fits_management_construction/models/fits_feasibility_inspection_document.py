from odoo import models, fields, api, _, exceptions

# Model Defect List / Daftar Cacat
class FeasibilityInspectionDocument(models.Model):
    _name = 'feasibility.inspection.document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Feasibility Inspection Document'
    _rec_name = 'no_pho'

    no_pho = fields.Char(string="PHO")
    submission_date = fields.Date(string="Submission Date")

    name_project          = fields.Many2one('project.project', string="Name Project", required=True)
    package               = fields.Char(string="Name Package")
    work_activities       = fields.Char(string="Work Activities")
    no_contract           = fields.Char(string="No Contract", readonly=True, required=True, copy=False, default='New')
    contract_date         = fields.Date(string="Contract Date")
    construction_provider = fields.Many2one('res.partner', string="Construction Provider")
    active = fields.Boolean(string="Active", default=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    feasibility_inspection_ids = fields.One2many('feasibility.inspection.detail', 'feasibility_inspection_id', string="Feasibility Inspection Detail")
    
    # Work Detail
    location            = fields.Char(string="Location")
    cost_center         = fields.Char(string="Cost Center")
    description         = fields.Text(string="Description")

    notes               = fields.Text(string="Notes Quality Defect")

    @api.model
    def create(self, vals):
        if vals.get('no_contract', 'New') == 'New':
            vals['no_contract'] = self.env['ir.sequence'].next_by_code('no.contract') or 'New'
        result = super(FeasibilityInspectionDocument, self).create(vals)
        return result

    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(FeasibilityInspectionDocument, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")

class FeasibilityInspectionDetail(models.Model):
    _name = 'feasibility.inspection.detail'
    _description = 'Feasibility Inspection Detail'
    _rec_name = 'inspection_item'

    feasibility_inspection_id  = fields.Many2one('feasibility.inspection.document', string="Feasibility Inspection Document")
    inspection_item            = fields.Char(string="Inspection Item")
    compliant_status           = fields.Boolean(string="Inbond Status")
    noncompliant_status        = fields.Boolean(string="noncompliant Status")

    @api.onchange('compliant_status')
    def _onchange_compliant_status(self):
        if self.compliant_status:
            self.noncompliant_status = False

    @api.onchange('noncompliant_status')
    def _onchange_noncompliant_status(self):
        if self.noncompliant_status:
            self.compliant_status = False