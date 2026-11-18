from odoo import http
from odoo.http import request
import base64

class StakeholderAnalysisController(http.Controller):
    @http.route('/download/stakeholder_analysis_excel/<int:record_id>', type='http', auth="user")
    def download_stakeholder_analysis_excel(self, record_id, **kwargs):
        record = request.env['stakeholder.analysis'].browse(record_id).exists()
        if not record:
            return request.not_found()
        record.check_access('read')
        if not record.excel_file:
            return request.not_found()

        # File response
        file_content = base64.b64decode(record.excel_file)
        file_name = record.excel_file_name or "Stakeholder.xlsx"
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={file_name}')
            ]
        )
