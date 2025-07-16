from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Computed field untuk menyimpan nama field grup dinamis
    dynamic_group_field = fields.Char("Management Construction", compute='_compute_dynamic_group_field')

    @api.depends('groups_id')  # Depend on the user group
    def _compute_dynamic_group_field(self):
        # Mengambil ID grup yang diperlukan
        user_group = self.env.ref('fits_management_construction.group_management_construction_user', raise_if_not_found=False)
        manager_group = self.env.ref('fits_management_construction.group_management_construction_manager', raise_if_not_found=False)

        # Membuat nama field berdasarkan ID grup
        if user_group and manager_group:
            self.dynamic_group_field = f"sel_groups_{user_group.id}_{manager_group.id}"
        else:
            self.dynamic_group_field = ""
