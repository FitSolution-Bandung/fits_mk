from odoo import http
from odoo.http import request
import json

class AnalysisRiskMitigationAPI(http.Controller):

    @http.route('/api/analysis_risk_mitigation', type='json', auth='public', methods=['POST'], csrf=False)
    def create_analysis_risk_mitigation(self, **kwargs):
        try:
            # Extract the required data from the POST request
            data = request.httprequest.get_json()

            # Validate that necessary fields are provided
            name = data.get('name')
            risk_mitigation_ids = data.get('risk_mitigation_ids', [])
            field_conditions_ids = data.get('field_conditions_ids', [])

            if not name:
                return json.dumps({'error': 'Name is required'})

            # Function to find the corresponding Many2one record based on the provided code
            def find_record_by_code(model, code_field, code_value):
                record = request.env[model].sudo().search([(code_field, '=', code_value)], limit=1)
                if record:
                    return record.id
                return None

            # Process the risk mitigation data to map code-based fields to ids
            risk_mitigation_data = []
            for rm in risk_mitigation_ids:
                likelihood_code = rm.get('likelihood')  # This is now a string, e.g., 'HIGH'
                impact_code = rm.get('impact')  # Same for other many2one fields
                risk_level_code = rm.get('risk_level')
                mitigation_code = rm.get('mitigation')

                # Find the ids based on the 'code' field or any unique field in the corresponding models
                likelihood_id = find_record_by_code('likelihood', 'code', likelihood_code)
                impact_id = find_record_by_code('impact', 'code', impact_code)
                risk_level_id = find_record_by_code('risk.scale', 'code', risk_level_code)
                mitigation_id = find_record_by_code('risk.mitigation.type', 'code', mitigation_code)

                # Add the processed risk mitigation data
                risk_mitigation_data.append({
                    'category': rm.get('category'),
                    'risk_identification': rm.get('risk_identification'),
                    'reason': rm.get('reason'),
                    'potential_impact': rm.get('potential_impact'),
                    'risk_code': rm.get('risk_code'),
                    'likelihood': likelihood_id,  # Now mapped to id
                    'impact': impact_id,          # Now mapped to id
                    'risk_score': rm.get('risk_score'),
                    'risk_level': risk_level_id,
                    'mitigation': mitigation_id,
                    'action': rm.get('action')
                })

            # Create the analysis.risk.mitigation record
            analysis = request.env['analysis.risk.mitigation'].sudo().create({
                'name': name,
                'risk_mitigation_ids': [(0, 0, rm) for rm in risk_mitigation_data],
                'field_conditions_ids': [(0, 0, fc) for fc in field_conditions_ids],
            })

            # Return success response
            return json.dumps({
                'success': True,
                'id': analysis.id,
                'message': 'Analysis Risk Mitigation created successfully'
            })

        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
