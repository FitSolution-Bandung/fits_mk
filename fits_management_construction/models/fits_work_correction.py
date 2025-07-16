from odoo import models, fields, api, _, exceptions

# Model Defect List / Daftar Cacat
class WorkCorrection(models.Model):
    _name = 'work.correction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Work Correction'
    _rec_name = 'name_project'

    name_project          = fields.Many2one('project.project', string="Name Project", required=True)
    package               = fields.Char(string="Work Package")
    location              = fields.Char(string="Location")
    inspection_date       = fields.Date(string="Inspection Date")
    inspection_by         = fields.Many2one('hr.employee', string="Inspection by")
    active = fields.Boolean(string="Active", default=True)
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    def write(self, vals):
        # Cek apakah status ingin diubah
        if 'status' in vals:
            # Pastikan hanya Manager yang bisa mengubah status
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(WorkCorrection, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")