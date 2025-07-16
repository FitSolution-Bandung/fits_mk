from odoo import models, fields, api, _, exceptions

# Model Defect List / Daftar Cacat
class DocumentInbondOutbond(models.Model):
    _name = 'document.inbond.outbond'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Document Inbond Outbond'
    _rec_name = 'no_doc_inoutbond'

    # name_project          = fields.Many2one('project.project', string="Name Project", required=True)
    # work                  = fields.Char(string="Work")
    no_doc_inoutbond   = fields.Char(string="No Doc In/Outbond", readonly=True, required=True, copy=False, default='New')
    active = fields.Boolean(string="Active", default=True)
    # date                  = fields.Date(string="Date")
    # month_name            = fields.Char(string="Month Name", compute="_compute_month_name")
    # day_name              = fields.Char(string="Day", compute="_compute_day_name", store=True, readonly=True)
    # location              = fields.Char(string="Location")
    # total                 = fields.Float(string="Total", compute="_compute_total", store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    document_inbond_outbond_ids = fields.One2many('document.inbond.outbond.detail', 'document_inbond_outbond_id', string="Document Inbond Outbond Detail")
 
    @api.model
    def create(self, vals):
        if vals.get('no_doc_inoutbond', 'New') == 'New':
            vals['no_doc_inoutbond'] = self.env['ir.sequence'].next_by_code('no.doc.inoutbond') or 'New'
        result = super(DocumentInbondOutbond, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(DocumentInbondOutbond, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")

class DocumentInbondOutbondDetail(models.Model):
    _name = 'document.inbond.outbond.detail'
    _description = 'Document Inbond Outbond Detail'
    _rec_name = 'no_doc'

    document_inbond_outbond_id  = fields.Many2one('document.inbond.outbond', string="Document Inbond Outbond")
    date                = fields.Date(string="Date")
    # no_agenda           = fields.Char(string="Quantity")
    no_doc              = fields.Char(string="No Document")
    summary             = fields.Char(string="Summary")
    source              = fields.Many2one('res.partner', string="Source")
    destination         = fields.Many2one('res.partner', string="Destination")
    inbond_status       = fields.Boolean(string="Inbond Status")
    outbond_status      = fields.Boolean(string="Outbond Status")

    @api.onchange('inbond_status')
    def _onchange_inbond_status(self):
        if self.inbond_status:
            self.outbond_status = False

    @api.onchange('outbond_status')
    def _onchange_outbond_status(self):
        if self.outbond_status:
            self.inbond_status = False