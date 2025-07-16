from odoo import http
from odoo.http import request, Response
import json
import logging
from datetime import date

_logger = logging.getLogger(__name__)

class CurveSController(http.Controller):
    @http.route(['/curve_s/data/<int:id>'], type='http', auth='user', csrf=False)
    def get_curve_s_data(self, id, **kw):
        try:
            curve = request.env['project.curve.s'].browse(id)
            if not curve.exists():
                return Response(
                    json.dumps({'error': 'Kurva tidak ditemukan'}),
                    content_type='application/json;charset=utf-8',
                    status=404
                )
            
            data = curve.get_curve_s_data()
            _logger.info(f"Data yang diterima untuk kurva ID {id}: {data}")

            # Mengecek jika data kurva kosong
            if not data.get('dates') or not data.get('plan_weights'):
                _logger.warning(f"Data untuk kurva ID {id} tidak lengkap: {data}")
                return Response(
                    json.dumps({'error': 'Data untuk kurva ini tidak lengkap'}),
                    content_type='application/json;charset=utf-8',
                    status=400
                )
            
            last_date = curve.get_last_updated_date_for_project()
            last_date_updated = last_date.isoformat()
            
            response = {
                'data': data,
                'project_name': curve.project_id.name,
                'last_updated_date': last_date_updated
                # 'last_updated_date': curve.get_last_updated_date_for_project()
            }

            # _logger.info(f"Response   untuk kurva ID {id}: {response}")
            
            return Response(
                json.dumps(response),
                content_type='application/json;charset=utf-8',
                status=200
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json;charset=utf-8',
                status=500
            )
        
    
    @http.route(['/gantt/data/<int:id>'], type='http', auth='user', csrf=False)
    def get_gantt_data(self, id, **kw):
        try:
            curve = request.env['project.curve.s'].browse(id)
            if not curve.exists():
                return Response(
                    json.dumps({'error': 'Kurva tidak ditemukan'}),
                    content_type='application/json;charset=utf-8',
                    status=404
                )
            
            data = curve.get_curve_s_data()
            # _logger.info(f"Data yang diterima untuk kurva ID {id}: {data}")

            # Mengecek jika data kurva kosong
            if not data.get('dates') or not data.get('plan_weights'):
                _logger.warning(f"Data untuk kurva ID {id} tidak lengkap: {data}")
                return Response(
                    json.dumps({'error': 'Data untuk kurva ini tidak lengkap'}),
                    content_type='application/json;charset=utf-8',
                    status=400
                )
            
            last_date = curve.get_last_updated_date_for_project()
            last_date_updated = last_date.isoformat()
            
            response = {
                'data': data,
                'project_name': curve.project_id.name,
                'last_updated_date': last_date_updated
                # 'last_updated_date': curve.get_last_updated_date_for_project()
            }

            # _logger.info(f"Response untuk kurva ID {id}: {response}")
            
            return Response(
                json.dumps(response),
                content_type='application/json;charset=utf-8',
                status=200
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json;charset=utf-8',
                status=500
            )
      
