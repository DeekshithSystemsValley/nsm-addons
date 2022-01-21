# -*- coding: utf-8 -*-
from odoo import http

# class NsmCrm(http.Controller):
#     @http.route('/nsm_crm/nsm_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nsm_crm/nsm_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('nsm_crm.listing', {
#             'root': '/nsm_crm/nsm_crm',
#             'objects': http.request.env['nsm_crm.nsm_crm'].search([]),
#         })

#     @http.route('/nsm_crm/nsm_crm/objects/<model("nsm_crm.nsm_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nsm_crm.object', {
#             'object': obj
#         })