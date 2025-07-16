from odoo import http
from odoo.http import request
import json

class DailyReportAPI(http.Controller):

    @http.route('/api/daily_report/get', type='http', auth='user', methods=['GET'], csrf=False)
    def get_daily_reports(self, **kwargs):
        daily_reports = request.env['daily.report'].sudo().search([])
        data = []

        products = request.env['product.template'].sudo().search([('rab_category', '=', 'material')])
        product_data = []

        for product in products:
            product_data.append({
                'id': product.id,
                'name': product.name,
            })

        for record in daily_reports:
            data.append({
                'no_dr': record.no_dr,
                'date': record.date.strftime('%Y-%m-%d'),
                'project': record.project.name,
                # 'provider': record.project.provider.display_name,
                # 'supervisory_consultant': record.project.supervisory_consultant.display_name,
                # 'planning_consultant': record.project.planning_consultant.display_name,
                # 'leader': record.leader.name,
                # 'supervisor': record.supervisor.name,
                'wbs_ids': [{'wbs_category': wbs.wbs_category.display_name, 'wbs': wbs.wbs.name, 'plan_weight': f'{wbs.plan_weight:.2f}'} for wbs in record.wbs_ids],
            })

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    @http.route('/api/daily_report', type='json', auth='user', methods=['POST'], csrf=False)
    def post_daily_report(self, **kwargs):
        required_fields = ['date', 'wbs_id', 'actual_weight']

        missing_fields = [field for field in required_fields if field not in kwargs]
        if missing_fields:
            return {'status': 400, 'error': f'Missing required fields: {", ".join(missing_fields)}'}

        try:
            # Mengambil WBS berdasarkan wbs_id yang diberikan
            wbs_record = request.env['wbs.model'].sudo().browse(kwargs['wbs_id'])
            if not wbs_record:
                return {'status': 404, 'error': 'WBS not found'}

            # Menyimpan actual_weight ke dalam daily report
            report = request.env['daily.report'].sudo().search([('date', '=', kwargs['date'])])
            if report:
                report.write({
                    'actual_weight': kwargs['actual_weight'],  # Misalnya field actual_weight ada di model daily.report
                    'wbs_ids': [(4, wbs_record.id)],  # Mengupdate relasi WBS jika perlu
                })

                return {'status': 201, 'message': 'Daily report updated successfully'}
            else:
                return {'status': 404, 'error': 'Daily report not found'}

        except Exception as e:
            return {'status': 500, 'error': str(e)}