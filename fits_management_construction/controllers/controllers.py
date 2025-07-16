# -*- coding: utf-8 -*-
# from odoo import http


# class FitsManagementConstruction(http.Controller):
#     @http.route('/fits_management_construction/fits_management_construction', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fits_management_construction/fits_management_construction/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fits_management_construction.listing', {
#             'root': '/fits_management_construction/fits_management_construction',
#             'objects': http.request.env['fits_management_construction.fits_management_construction'].search([]),
#         })

#     @http.route('/fits_management_construction/fits_management_construction/objects/<model("fits_management_construction.fits_management_construction"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fits_management_construction.object', {
#             'object': obj
#         })

