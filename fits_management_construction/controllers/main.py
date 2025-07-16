from odoo import http
from odoo.http import request

class CurveSController(http.Controller):
    @http.route('/curve_s/data/<int:curve_id>', type='json', auth='user')
    def get_curve_s_data(self, curve_id):
        curve = request.env['project.curve.s'].browse(curve_id)
        data = [{'date': line.date, 'actual_weight': line.actual_weight, 'plan_weight': line.plan_weight, 'plan_weight_b': line.plan_weight_b}
                for line in curve.line_ids]
        return {'result': data}
