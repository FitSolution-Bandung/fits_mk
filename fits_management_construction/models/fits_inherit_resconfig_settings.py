from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    gemini_api_key = fields.Char(string = "Gemini API Key", help="Type Gemini API key here", config_parameter="fits_management_construction.gemini_api_key")

    # group_uom = fields.Boolean(string="Enable Custom UoM", config_parameter="fits_management_construction.group_uom")

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     res['group_uom'] = self.env['ir.config_parameter'].sudo().get_param('fits_management_construction.group_uom', default=False)
    #     return res

    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     # Simpan nilai group_uom ke parameter konfigurasi
    #     self.env['ir.config_parameter'].sudo().set_param('fits_management_construction.group_uom', self.group_uom)
        
    #     # Update tampilan menu berdasarkan nilai group_uom
    #     self._update_uom_menu(self.group_uom)

    # @api.model
    # def _update_uom_menu(self, is_enabled):
    #     """ Memperbarui menu berdasarkan pengaturan group_uom """
    #     menu_uom = self.env.ref('fits_management_construction.menu_uom_category', raise_if_not_found=False)
    #     if menu_uom:
    #         menu_uom.active = is_enabled