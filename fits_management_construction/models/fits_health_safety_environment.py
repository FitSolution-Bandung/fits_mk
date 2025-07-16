from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
# from odoo.addons.fits_management_construction.models.utils.gemini_helper import generate_text
# import re

class HealthSafetyEnvironment(models.Model):
    _name = 'health.safety.environment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Health Safety Environment'
    _rec_name = 'no_hse'

    no_hse = fields.Char(string="No JSA", readonly=True, required=True, copy=False, default='New')
    work_type = fields.Char(string='Work Type')
    work_location = fields.Text(string='Work Location')
    date = fields.Date(string='Date')
    protective_equip = fields.Char(string='Protective Equipment/APD')
    tools = fields.Char(string='Tools')
    procedure = fields.Char(string='Procedure')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    active = fields.Boolean(string="active", default=True)

    #FIELD EMERGENCY CONTACT
    company_representative = fields.Many2one('hr.employee', string='Employee')
    company_representative_phone = fields.Char(related='company_representative.private_phone',
                                               string='Phone', readonly=True)

    contractor_representative = fields.Many2one('res.partner', string='Contractor')
    contractor_representative_phone = fields.Char(related='contractor_representative.phone',
                                                  string='Phone', readonly=True)

    # FIELD GENERAL DANGERS
    danger_1 = fields.Boolean(string='Danger of Falling/Tripping/Slipping')
    danger_2 = fields.Boolean(string='Danger of being Pinched/Entangled')
    danger_3 = fields.Boolean(string='Lack of Lighting')
    danger_4 = fields.Boolean(string='Lift/Bend/Pull/Rotate')
    danger_5 = fields.Boolean(string='Uneven/Graded Track')
    danger_6 = fields.Boolean(string='Rotating/Moving Equipment Parts')
    danger_7 = fields.Boolean(string='Hot Surfaces')
    danger_8 = fields.Boolean(string='Bad/Extreme Weather')
    danger_9 = fields.Boolean(string='Animal Danger')
    danger_10 = fields.Boolean(string='Noisy')
    danger_11 = fields.Boolean(string='Vibration')
    danger_12 = fields.Boolean(string='Vehicle Danger')
    other = fields.Boolean(string='Other')
    notes = fields.Char(string='Notes', help="Describe other danger if applicable")

    @api.constrains('other', 'notes')
    def _check_notes(self):
        for record in self:
            if record.other and not record.notes:
                raise ValidationError("Please provide details in the 'Notes' field when 'Other' is selected.")
        
    # danger_ids = fields.Many2many('general.danger', string='General Dangers')

    # analysis_risk_mitigation_id = fields.Many2one('analysis.risk.mitigation', string="Analysis Risk Mitigation")


    # Relasi dengan Work Stages
    work_stages_ids = fields.One2many('work.stages', 'hse_id', string='Work Stages')

    # Relasi dengan Emergency Contact
    emergency_contact_ids = fields.One2many('emergency.contact', 'hse_id', string='Emergency Contact')

    # Relasi dengan General Dangers
    # general_dangers_id = fields.One2many('general.dangers', 'hse_ids', string='General Dangers')

    simops_ids = fields.One2many('simops', 'hse_id', string='SIMOPs')

    @api.model
    def create(self, vals):
        if vals.get('no_hse', 'New') == 'New':
            vals['no_hse'] = self.env['ir.sequence'].next_by_code('no.hse') or 'New'
        result = super(HealthSafetyEnvironment, self).create(vals)
        return result
    
    def write(self, vals):
        if 'status' in vals:
            if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
                raise exceptions.AccessError("Only managers can change the status.")
        return super(HealthSafetyEnvironment, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_canceled(self):
        self.status = 'cancelled'
        self.message_post(body=f"Status changed to Cancelled by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")

    # def create_arm(self):
    #     self.ensure_one()

    #     return {
    #         'name': 'Analysis & Risk Mitigation',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('fits_management_construction.view_analysis_risk_mitigation_form').id,
    #         'res_model': 'analysis.risk.mitigation',
    #         'context': {'default_hse_id': self.id},
    #     }

    # def get_analysis_risk_mitigation(self):
    #     self.ensure_one()

    #     views = [(self.env.ref('fits_management_construction.view_analysis_risk_mitigation_tree').id, 'tree'),
    #              (self.env.ref('fits_management_construction.view_analysis_risk_mitigation_form').id, 'form')]

    #     return {
    #         'name': 'Analysis & Risk Mitigation',
    #         'view_type': 'form',
    #         'view_mode': 'form,tree',
    #         'view_id': False,
    #         'res_model': 'analysis.risk.mitigation',
    #         'views': views,
    #         'domain': [
    #             ('id', '=', self.analysis_risk_mitigation_id.id)
    #         ],
    #         'type': 'ir.actions.act_window',
    #     }

class WorkStages(models.Model):
    _name = 'work.stages'
    _description = 'Work Stages'

    work_stages = fields.Text(string='Work Stages')
    danger_information = fields.Text(string='Danger Information')
    protection_prevention = fields.Text(string='Protection & Prevention')
    person_responsible_apd = fields.Text(string='Responsible for APD')
    responsible_verifying_equip = fields.Text(string='Responsible for Equipment Verification')
    risk = fields.Char(string='Risk Level')
    job_checking = fields.Boolean(string='Job Checking')

    hse_id = fields.Many2one('health.safety.environment', string='HSE Reference')

    # @staticmethod
    # def _clean_text(text):
    #     """
    #     Remove non-alphanumeric characters except spaces from the given text.
    #     """
    #     # Keep only alphanumeric characters and spaces
    #     return re.sub(r"[^a-zA-Z0-9\s\(\)]", "", text).strip()

    # @api.onchange('work_stages')
    # def _onchange_risk_identification(self):
    #     """
    #     Automatically generate an action plan based on the risk identification.
    #     """

    #     api_key = self.env['ir.config_parameter'].sudo().get_param('fits_management_construction.gemini_api_key')
    #     if not api_key:
    #         raise UserError("Gemini API Key is not configured in the system settings.")

    #     for record in self:
    #         if record.work_stages:
    #             prompt = f"""
    #             Saya sedang menyusun Job Safety Analysis (JSA) untuk tahap pekerjaan berikut di proyek konstruksi:

    #             Tahap pekerjaan: {record.work_stages}

    #             Berdasarkan tahap pekerjaan ini, tolong berikan deskripsi singkat yang mencakup:
    #             1. Bahaya utama yang mungkin terjadi selama pelaksanaan pekerjaan ini.
    #             2. Langkah-langkah pencegahan atau pelindung untuk mengurangi risiko dari bahaya tersebut.
    #             3. Siapa yang bertanggung jawab atas penerapan APD selama tahap pekerjaan ini.
    #             4. Siapa yang bertanggung jawab untuk memverifikasi bahwa langkah pencegahan telah diterapkan.
    #             5. Tingkat risiko (Contoh: High Risk (H), Significant Risk (S), atau Low Risk (L)) berdasarkan potensi bahaya dan langkah mitigasi, lalu tidak perlu ada penjelasan cukup pilih diantara ke 3 contoh itu saja dan tolong ingat sesuaikan dengan contoh jawabannya (bahasa inggris).

    #             Jawab dengan deskripsi singkat dalam format berikut:
    #             - Bahaya: <deskripsi bahaya>
    #             - Pencegahan: <deskripsi langkah pencegahan>
    #             - Penanggung Jawab Penerapan APD: <penanggung jawab penerapan APD>
    #             - Penanggung Jawab Verifikasi: <penanggung jawab verifikasi>
    #             - Tingkat Risiko: <tingkat risiko, contoh: High Risk (H), Significant Risk (S), atau Low Risk (L)>
    #             """
    #             try:
    #                 response = generate_text(prompt, api_key)
    #                 danger, protection, respon_apd, respon_equip, risk = self._parse_response(response)
                    
    #                 record.danger_information = danger
    #                 record.protection_prevention = protection
    #                 record.person_responsible_apd = respon_apd
    #                 record.responsible_verifying_equip = respon_equip
    #                 record.risk = risk
    #             except Exception as e:
    #                 record.danger_information = "Error processing danger information."
    #                 record.protection_prevention = "Error processing danger information."
    #                 record.person_responsible_apd = "Error processing danger information."
    #                 record.responsible_verifying_equip = "Error processing danger information."
    #                 record.risk = f"Error Generating: {e}"
    #         else:
    #             record.danger_information = ""
    #             record.protection_prevention = ""
    #             record.person_responsible_apd = ""
    #             record.responsible_verifying_equip = ""
    #             record.risk = ""
    
    # def _parse_response(self, response):
    #     """
    #     Parse the Gemini AI response into cause, impact, and actions.
    #     """
    #     danger = ""
    #     protection = ""
    #     respon_apd = ""
    #     respon_equip = ""
    #     risk = ""
        
    #     if "Bahaya:" in response:
    #         danger = response.split("Bahaya:")[1].split("Pencegahan:")[0].strip()
    #         danger = self._clean_text(danger)
        
    #     if "Pencegahan:" in response:
    #         protection = response.split("Pencegahan:")[1].split("Penanggung Jawab Penerapan APD:")[0].strip()
    #         protection = self._clean_text(protection)
        
    #     if "Penanggung Jawab Penerapan APD:" in response:
    #         respon_apd = response.split("Penanggung Jawab Penerapan APD:")[1].split("Penanggung Jawab Verifikasi:")[0].strip()
    #         respon_apd = self._clean_text(respon_apd)
        
    #     if "Penanggung Jawab Verifikasi:" in response:
    #         respon_equip = response.split("Penanggung Jawab Verifikasi:")[1].split("Tingkat Risiko:")[0].strip()
    #         respon_equip = self._clean_text(respon_equip)
        
    #     if "Tingkat Risiko:" in response:
    #         risk = response.split("Tingkat Risiko:")[1].strip()
    #         risk = self._clean_text(risk)

    #     # logging.debug(f"Extracted Actions: {action}")
        
    #     return danger, protection, respon_apd, respon_equip, risk

class EmergencyContact(models.Model):
    _name = 'emergency.contact'
    _description = 'Emergency Contact'

    emergency_response_team = fields.Many2one('hr.employee', string='Employee')
    emergency_response_team_phone = fields.Char(related='emergency_response_team.private_phone',
                                                string='Phone', readonly=True)

    hse_id = fields.Many2one('health.safety.environment', string='HSE Reference')

# class GeneralDangers(models.Model):
#     _name = 'general.dangers'
#     _description = 'General Dangers'

#     danger_1 = fields.Boolean(string='Danger of Falling/Tripping/Slipping')
#     danger_2 = fields.Boolean(string='Danger of being Pinched/Entangled')
#     danger_3 = fields.Boolean(string='Lack of Lighting')
#     danger_4 = fields.Boolean(string='Lift/Bend/Pull/Rotate')
#     danger_5 = fields.Boolean(string='Uneven/Graded Track')
#     danger_6 = fields.Boolean(string='Rotating/Moving Equipment Parts')
#     danger_7 = fields.Boolean(string='Hot Surfaces')
#     danger_8 = fields.Boolean(string='Bad/Extreme Weather')
#     danger_9 = fields.Boolean(string='Animal Danger')
#     danger_10 = fields.Boolean(string='Noisy')
#     danger_11 = fields.Boolean(string='Vibration')
#     danger_12 = fields.Boolean(string='Vehicle Danger')
#     other = fields.Boolean(string='Other')

#     hse_ids = fields.Many2one('health.safety.environment', string='HSE Reference', ondelete='cascade')

class SIMOPs(models.Model):
    _name = 'simops'
    _description = 'SIMOPs'

    hse_id = fields.Many2one('health.safety.environment', string='HSE Reference')
    safety_man = fields.Many2one('hr.employee', string='Safety Man')
    desc = fields.Text(string='Description')