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
import odoo.addons.decimal_precision as dp

class Template(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float('Cost', digits=dp.get_precision('Product Price'),
                                  help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders.",)



class Product(models.Model):
    _inherit = 'product.product'

    avail_supplier_portal = fields.Selection([('marketing', 'Marketing'),
                                               ('editorial', 'Editorial')],
                                              "Available Supplier Portal",)



class Category(models.Model):
    _inherit = "product.category"

    @api.model
    def _supplier_category_search(self, operator, operand):
        user = self.env.user
        supplier = user.partner_id  # partner_id is required on users
        if not supplier.product_category_ids:
            return [('id', '=', False)]
        cat_ids = [cat.id for cat in supplier.product_category_ids]
        portal_category_ids = self.search([('supportal', '=', True)])
        portal_category_ids.extend(cat_ids.ids)
        return [('id', 'in', portal_category_ids)]


    supportal = fields.Boolean('Parent Portal Productcategorieen',
                               help="Indicator that determines the role of this category as parent of supplier portal categories.")
    supp_category_ids = fields.Many2many('res.partner','partner_category_rel','product_category_id','partner_id',
                                            'Supplier IDs', copy=True)

    @api.model
    def search(self, args, offset=0, limit=0, order=None, count=False):
        if self.env.user.has_group('nsm_supplier_portal.group_module_supplier_portal_user'):
            args.append(('supp_category_ids', 'in', self.env.user.partner_id.ids))
        return super(Category, self).search(args, offset=offset, limit=limit, order=order, count=count)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
