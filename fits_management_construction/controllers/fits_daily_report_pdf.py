from odoo import http
from odoo.http import request
import base64

class DailyReportController(http.Controller):

    @http.route('/api/daily_report/<int:record_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def fetch_daily_report(self, record_id):
        try:
            # Ambil record berdasarkan ID
            # report_id = int(record_id)
            report_name = 'fits_management_construction.report_daily_report_template'
            model = 'daily.report'

            # Pastikan record ada
            record = request.env[model].browse(record_id)
            if not record.exists():
                return request.make_response(
                    "Record not found",
                    headers={'Content-Type': 'text/plain'},
                    status=404
                )

            # Render laporan
            pdf = request.env['ir.actions.report']._render_qweb_pdf(report_name, [int(record_id)])[0]
            pdf_base64 = base64.b64encode(pdf).decode('utf-8')

            return request.make_response(
                pdf,
                headers={
                    'Content-Type': 'application/pdf',
                    'Content-Disposition': f'attachment; filename="daily_report_{record_id}.pdf"',
                }
            )
        except Exception as e:
            return request.make_response(
                str(e),
                headers={'Content-Type': 'text/plain'},
                status=500
            )