# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError
# from odoo.addons.fits_management_construction.models.utils.gemini_helper import generate_text
# import re
# import logging
# from openai import OpenAI

class AnalysisRiskMitigation(models.Model):
    _name = 'analysis.risk.mitigation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Analysis & Risk Mitigation'
    _rec_name = 'name'

    no_mitigation = fields.Char(string="No Mitigation", readonly=True, required=True, copy=False, default='New')
    name = fields.Char(string='Project Name', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('monitoring', 'Monitoring'),
        ('done', 'Done')
    ], string='Status', default='draft')
    risk_mitigation_ids = fields.One2many('risk.mitigation', 'analysis_id', string='Risk Mitigations')
    field_conditions_ids = fields.One2many('field.conditions', 'analysis_id', string='Field Conditions')
    material_distribution_ids = fields.One2many('material.distribution', 'analysis_id', string='Material Distributions')
    active = fields.Boolean(string="Active", default=True)
    # hse_id = fields.One2many('health.safety.environment', 'analysis_ris  k_mitigation_id', string="Health Safety Environment")

    #matrix puyeng tapi aman
    def get_riskmap_matrix(self):
        matrix = [[0 for _ in range(5)] for _ in range(5)]

        for risk in self.risk_mitigation_ids:
            likelihood_no = int(risk.likelihood.no) if risk.likelihood.no and risk.likelihood.no.isdigit() else 1
            impact_no = int(risk.impact.no) if risk.impact.no and risk.impact.no.isdigit() else 1

            i = impact_no - 1
            j = likelihood_no - 1

            if 0 <= i < 5 and 0 <= j < 5:
                matrix[i][j] += 1

        return matrix
    
    @api.model
    def create(self, vals):
        if vals.get('no_mitigation', 'New') == 'New':
            vals['no_mitigation'] = self.env['ir.sequence'].next_by_code('no.mitigation') or 'New'
        result = super(AnalysisRiskMitigation, self).create(vals)
        return result

    # def write(self, vals):
    #     # Cek apakah status ingin diubah
    #     if 'status' in vals:
    #         # Pastikan hanya Manager yang bisa mengubah status
    #         if not self.env.user.has_group('fits_management_construction.group_management_construction_manager'):
    #             raise exceptions.AccessError("Only managers can change the status.")
    #     return super(AnalysisRiskMitigation, self).write(vals)

    def action_confirm(self):
        self.status = 'confirm'
        self.message_post(body=f"Status changed to Confirmed by {self.env.user.name}")

    def action_done(self):
        self.status = 'done'
        self.message_post(body=f"Status changed to Done by {self.env.user.name}")

    def action_draft(self):
        self.status = 'draft'
        self.message_post(body=f"Status changed to Draft by {self.env.user.name}")

    def action_monitoring(self):
        self.status = 'monitoring'
        self.message_post(body=f"Status changed to Monitoring by {self.env.user.name}")

    # def create_hse(self):
    #     self.ensure_one()

    #     return {
    #         'name': 'Health Safety Environment',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('fits_management_construction.view_health_safety_environment_form').id,
    #         'res_model': 'health.safety.environment',
    #         'context': {'default_analysis_risk_mitigation_id': self.id},
    #     }

    # def get_hse(self):
    #     self.ensure_one()

    #     views = [(self.env.ref('fits_management_construction.view_health_safety_environment_tree').id, 'tree'),
    #              (self.env.ref('fits_management_construction.view_health_safety_environment_form').id, 'form')]

    #     return {
    #         'name': 'Health Safety Environment',
    #         'view_type': 'form',
    #         'view_mode': 'form,tree',
    #         'view_id': False,
    #         'res_model': 'health.safety.environment',
    #         'views': views,
    #         'domain': [
    #             ('analysis_risk_mitigation_id', '=', self.id)
    #         ],
    #         'type': 'ir.actions.act_window',
    #     }

class RiskMitigation(models.Model):
    _name = 'risk.mitigation'
    _description = 'Risk Mitigation'

    analysis_id = fields.Many2one('analysis.risk.mitigation', string='Analysis')
    category = fields.Char(string='Category')
    risk_identification = fields.Char(string='Risk Identification')
    reason = fields.Char(string='Reason')
    potential_impact = fields.Text(string='Potential Impact')
    risk_code = fields.Char(string='Risk Code')
    likelihood = fields.Many2one('likelihood', string='Likelihood')
    impact = fields.Many2one('impact', string='Impact')
    risk_score = fields.Char(string='Risk Score', compute='_compute_risk_score')
    risk_level = fields.Many2one('risk.scale', string='Risk Level', compute='_compute_risk_level')
    mitigation = fields.Many2one('risk.mitigation.type', string='Mitigation Type')
    action = fields.Text(string='Action')

    @api.depends('likelihood', 'impact')
    def _compute_risk_score(self):
        for record in self:
            if record.likelihood and record.impact:
                likelihood_value = getattr(record.likelihood, 'no', 0)
                impact_value = getattr(record.impact, 'no', 0)
                try:
                    risk_score = int(likelihood_value) * int(impact_value)
                    record.risk_score = str(risk_score)
                except (ValueError, TypeError):
                    record.risk_score = '0'
            else:
                record.risk_score = '0'
                
    @api.depends('risk_score')
    def _compute_risk_level(self):
        for record in self:
            if record.risk_score:
                try:
                    record.risk_level = self.env['risk.scale'].search([
                        ('scale_from', '<=', int(record.risk_score)),
                        ('scale_to', '>=', int(record.risk_score))
                    ], limit=1)
                except ValueError:
                    record.risk_level = False
            else:
                record.risk_level = False

    # @staticmethod
    # def _clean_text(text):
    #     # """
    #     # Remove non-alphanumeric characters except spaces from the given text.
    #     # """
    #     # Keep only alphanumeric characters and spaces
    #     return re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip()

    # @api.onchange('risk_identification')
    # def _onchange_risk_identification(self):
    #     """
    #     Automatically generate an action plan based on the risk identification.
    #     """
    #     # Fetch Gemini API key from system parameters
    #     api_key = self.env['ir.config_parameter'].sudo().get_param('fits_management_construction.gemini_api_key')
    #     if not api_key:
    #         raise UserError("Gemini API Key is not configured in the system settings.")

    #     # Generate action plan if risk_identification is filled
    #     for record in self:
    #         if record.risk_identification:
    #             prompt = f"""
    #             Berdasarkan identifikasi risiko berikut dalam konteks manajemen konstruksi, mohon berikan:
    #             1. Penyebab risiko ini (bentuk deskriptif secara singkat).
    #             2. Potensi dampak dari risiko ini (3 poin dampak secara singkat).
    #             3. Tiga poin tindakan singkat untuk mengurangi risiko ini, ingat! singkat saja ya.
    #             4. Berikan nilai Likelihood (1-5) untuk kemungkinan risiko terjadi.
    #             5. Berikan nilai Impact (1-5) untuk dampak yang mungkin ditimbulkan oleh risiko ini.
    #             6. Berikan kode risiko yang sesuai (contoh: RIS-01, dan seterusnya (harus berbeda dari yang sebelumnya anda kirim)).
    #             7. Berikan Mitigation Type (contoh: Risk Avoidance, Risk Transfer, Risk Reduction, Risk Acceptance, Risk Acceptance (Positive Risk)) jawaban diambil dari kelima contoh tersebut.

    #             Kategori Risiko: {record.category}
    #             Identifikasi Risiko: {record.risk_identification}

    #             Harap berikan respons dalam format berikut:
    #             Penyebab: <penyebab di sini>
    #             Dampak:
    #             - Dampak 1
    #             - Dampak 2
    #             - Dampak 3
    #             Tindakan:
    #             - Tindakan 1
    #             - Tindakan 2
    #             - Tindakan 3
    #             Likelihood: <nilai 1-5>
    #             Impact: <nilai 1-5>
    #             Kode Risiko: <kode di sini>
    #             Mitigation Type: <mitigation type di sini>
    #             """

    #             # try:
    #             #     response = generate_text(prompt, api_key)
    #             #     record.action = response
    #             # except Exception as e:
    #             #     record.action = f"Error generating action: {e}"
    #             try:
    #                 # Call the generate_text function to get the response from Gemini AI
    #                 response = generate_text(prompt, api_key)
                    
    #                 # Split the response into cause, impact, and actions
    #                 reason, potential_impact, action, likelihood, impact, risk_code, mitigation = self._parse_response(response)
                    
    #                 # Assign the parsed values to the respective fields
    #                 record.reason = reason
    #                 record.potential_impact = potential_impact
    #                 record.action = action  # Join actions into a single string separated by new lines
    #                 record.likelihood = likelihood
    #                 record.impact = impact
    #                 record.risk_code = risk_code
    #                 record.mitigation = mitigation
    #             except Exception as e:
    #                 record.reason = "Error processing cause."
    #                 record.potential_impact = "Error processing impact."
    #                 record.action = f"Error generating action: {e}"
    #                 record.likelihood = 0
    #                 record.impact = 0
    #                 record.risk_code = "Error generating risk code."
    #                 record.mitigation = "Error generating mitigation type."
    #         else:
    #             record.reason = ""
    #             record.potential_impact = ""
    #             record.action = ""
    #             record.likelihood = 1
    #             record.impact = 1
    #             record.risk_code = ""
    #             record.mitigation = ""
    
    # def _parse_response(self, response):
    #     """
    #     Parse the Gemini AI response into cause, impact, and actions.
    #     """
    #     reason = ""
    #     potential_impact = ""
    #     action = ""
    #     likelihood = ""
    #     impact = ""
    #     risk_code = ""
    #     mitigation = ""

        
    #     if "Likelihood:" in response:
    #         likelihood = response.split("Likelihood:")[1].split("Impact:")[0].strip()
    #         likelihood = self._clean_text(likelihood)
        
    #     if "Impact:" in response:
    #         impact = response.split("Impact:")[1].split("Kode Risiko:")[0].strip()
    #         impact = self._clean_text(impact)
        
    #     if "Kode Risiko:" in response:
    #         risk_code = response.split("Kode Risiko:")[1].split("Mitigation Type:")[0].strip()
    #         risk_code = self._clean_text(risk_code)

    #     if "Mitigation Type:" in response:
    #         mitigation = response.split("Mitigation Type:")[1].strip()
    #         mitigation = self._clean_text(mitigation)
        
    #     if "Penyebab:" in response:
    #         reason = response.split("Penyebab:")[1].split("Dampak:")[0].strip()
    #         reason = self._clean_text(reason)
        
    #     if "Dampak:" in response:
    #         potential_impact = response.split("Dampak:")[1].split("Tindakan:")[0].strip()
    #         potential_impact = self._clean_text(potential_impact)
        
    #     if "Tindakan:" in response:
    #         action = response.split("Tindakan:")[1].split("Likelihood:")[0].strip()
    #         action = self._clean_text(action)
    #         # [self._clean_text(action) for action in actions_text.split("\n") if action.strip()]

    #     likelihood_id = self._get_likelihood_id(likelihood)
    #     impact_id = self._get_impact_id(impact)
    #     mitigation_id = self._get_mitigation_id(mitigation)
    #     # logging.debug(f"Extracted Actions: {action}")
        
    #     return reason, potential_impact, action, likelihood_id, impact_id, risk_code, mitigation_id

    # def _get_mitigation_id(self, mitigation):
    #     mitigation_record = self.env['risk.mitigation.type'].search([('name', '=', mitigation)], limit=1)

    #     if mitigation_record:
    #         return mitigation_record.id
    #     else:
    #         return None

    # def _get_likelihood_id(self, likelihood_value):
    #     """
    #     Convert the likelihood value (1-5) to the corresponding Many2one ID for the likelihood model
    #     based on the 'no' field.
    #     """
    #     # Search for the record in the 'likelihood' model based on the 'no' field value
    #     likelihood_record = self.env['likelihood'].search([('no', '=', likelihood_value)], limit=1)
        
    #     if likelihood_record:
    #         return likelihood_record.id
    #     else:
    #         return None  # Return None or default ID if no matching record found

    # def _get_impact_id(self, impact_value):
    #     """
    #     Convert the impact value (1-5) to the corresponding Many2one ID for the impact model
    #     based on the 'no' field value.
    #     """
    #     # Search for the record in the 'impact' model based on the 'no' field value
    #     impact_record = self.env['impact'].search([('no', '=', impact_value)], limit=1)
        
    #     if impact_record:
    #         return impact_record.id
    #     else:
    #         return None  # Return None or default ID if no matching record found


    # @api.onchange('risk_identification')
    # def generate_action_suggestion(self):
    #     openai_api_key = "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"  # Mengambil API key dari variabel lingkungan
    #     # openai_org_key = "org-wDFeqJ9bCffVTD7dN4x3hHYJ"
    #     if not openai_api_key:
    #         self.action = "Error: OpenAI API key not found in environment variables."
    #         return

    #     if self.risk_identification:
    #         client = OpenAI(api_key=openai_api_key)

    #         for record in self:
    #             prompt = f"Provide a risk mitigation action for: {record.risk_identification}"
    #             try:
    #                 stream = client.chat.completions.create(
    #                     model="gpt-3.5-turbo",
    #                     messages=[{"role": "user", "content": prompt}],
    #                     stream=True
    #                 )

    #                 generated_content = ""
    #                 for chunk in stream:
    #                     if "content" in chunk.choices[0].delta:
    #                         generated_content += chunk.choices[0].delta["content"]

    #                 record.action = generated_content

    #             except Exception as e:
    #                 record.action = f"Error fetching suggestions: {str(e)}"
    

class FieldConditions(models.Model):
    _name = 'field.conditions'
    _description = 'Field Conditions'

    analysis_id = fields.Many2one('analysis.risk.mitigation', string='Analysis')
    condition = fields.Many2one('field.condition.type', string='Condition')
    description = fields.Char(string='Description')

class MaterialDistribution(models.Model):
    _name = 'material.distribution'
    _description = 'Material Distribution'

    analysis_id = fields.Many2one('analysis.risk.mitigation', string='Analysis')
    attachment = fields.Binary(string='Attachment', attachment=True)
    file_name = fields.Char(string="File Name")