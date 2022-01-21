# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 BAS Solutions
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _

class Partner(models.Model):
    _inherit = 'res.partner'

    reuse = fields.Boolean('Reuse-authorization', default=True)
    var_ok = fields.Boolean('VAR-verklaring OK')
    analytic_account_ids = fields.Many2many('account.analytic.account','partner_analytic_rel','partner_id','analytic_account_id',
                                            'Titles/Departments', copy=True)
    product_category_ids = fields.Many2many('product.category','partner_category_rel','partner_id','product_category_id',
                                            'Cost Categories', copy=True)
    fax = fields.Char(string="Fax")


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """
        Overrides orm field_view_get.
        @return: Dictionary of Fields, arch and toolbar.
        """

        res = {}
        res = super(Partner, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if not self._context.get('is_portal'):
            return res
        res['toolbar'] = {'print': [], 'other':[]}
        return res

    '''
    def create_supplier_user(self, cr, uid, ids, context={}):
        if not context:
            context = {}
        partner_ids = []
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.user_create:
                continue
            user_pool = self.pool.get('res.users')
            user_ids = user_pool.search(cr, uid, [('name', '=', obj.name)], context=context)
            if user_ids:
                raise osv.except_osv(_('Error!'), _('%s user is already created' % obj.name))
            login_name = ''.join(e for e in obj.name if e.isalnum())
            user_id = user_pool.create(cr, uid, {
                'login': login_name,
                'partner_id': obj.id,
                'tz': context['tz']
            }, context=context)
            partner_ids.append(user_id)
            self.write(cr, uid, obj.id, {
                'user_create': True,
            }, context=context)
        user_pool.action_reset_password(cr, uid, partner_ids, context)
    '''



class Company(models.Model):
    _inherit = 'res.company'

    data_fname = fields.Char("File Name")
    supplier_terms = fields.Binary("Supplier Invoice Reuse-authorization File")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
