from babel.dates import format_date
from datetime import datetime
from odoo import models, fields, api, exceptions

# Model Defect List / Daftar Cacat
class WorkRequest(models.Model):
    _name = 'work.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Work Request'
    _rec_name = 'name_project'

    name_project          = fields.Many2one('project.project', string="Name Project", required=True)
    package               = fields.Char(string="Name Package")
    work_activities       = fields.Char(string="Work Activities")
    no_contract           = fields.Char(string="No Contract", readonly=True, required=True, copy=False, default='New')
    contract_date         = fields.Date(string="Date")
    construction_provider = fields.Many2one('res.partner', string="Construction Provider")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    work_detail_ids = fields.Many2one('work.request.detail', string="Work Details")
    document_status_ids = fields.One2many('document.status', 'work_request_id', string="Document Status")
    location_ids = fields.One2many('location.work.request', 'work_request_id', string="Document Status")
    active = fields.Boolean(string="Active", default=True)


    # Work Request Detail
    work_detail         = fields.Text(string="Work Detail")
    start_date          = fields.Date(string="Start Date")
    finish_date         = fields.Date(string="Finish Date")
    notes               = fields.Char(string="Notes")

    @api.model
    def create(self, vals):
        if vals.get('no_contract', 'New') == 'New':
            vals['no_contract'] = self.env['ir.sequence'].next_by_code('no.contract') or 'New'
        result = super(WorkRequest, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(WorkRequest, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")
    
# class WorkRequestDetail(models.Model):
#     _name = 'work.request.detail'
#     _description = 'Work Request Detail'
#     _rec_name = 'work_detail'

    # work_request_id     = fields.One2many('work.request', string="Work Request")
    # work_detail         = fields.Text(string="Work Detail")
    # start_date          = fields.Date(string="Start Date")
    # finish_date         = fields.Date(string="Finish Date")
    # notes               = fields.Char(string="Notes")

class DocumentStatus(models.Model):
    _name = 'document.status'
    _description = 'Document Status'
    _rec_name = 'document'

    work_request_id     = fields.Many2one('work.request', string="Work Request")
    document            = fields.Char(string="Document")
    status              = fields.Char(string="Status")
    date                = fields.Date(string="Date")
    reference           = fields.Char(string="Reference")
    verification        = fields.Char(string="Verification")

class LocationWorkRequest(models.Model):
    _name = 'location.work.request'
    _description = 'Location Work Request'
    _rec_name = 'location'

    work_request_id = fields.Many2one('work.request', string="Work Request Detail")
    location               = fields.Char(string="Location")
