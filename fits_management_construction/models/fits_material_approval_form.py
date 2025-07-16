from odoo import models, fields, exceptions

# Model Defect List / Daftar Cacat
class MaterialApprovalForm(models.Model):
    _name = 'material.approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Material Approval'
    _rec_name = 'no_doc'

    name_project          = fields.Many2one('project.project', string="Name Project", required=True)
    location              = fields.Char(string="Location")
    active                = fields.Boolean(string="Active", default=True)
    no_doc                = fields.Char(string="No Document Report", readonly=True, required=True, copy=False, default='New')
    status                = fields.Selection([
                                ('draft', 'Draft'),
                                ('confirm', 'Confirmed'),
                                ('cancelled', 'Cancelled')
                            ], string='Status', default='draft')
    name_package          = fields.Char(string="Package")
    date                  = fields.Date(string="Date")
    name_subpackage       = fields.Char(string="Sub Package")
    
    def create(self, vals):
        if vals.get('no_doc', 'New') == 'New':
            vals['no_doc'] = self.env['ir.sequence'].next_by_code('no.doc') or 'New'
        result = super(MaterialApprovalForm, self).create(vals)
        return result
    
    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(MaterialApprovalForm, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")