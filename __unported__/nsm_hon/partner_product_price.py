# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Magnus www.magnus.nl
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


from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class partner_product_price(orm.Model):

    _name = "partner.product.price"

    _columns = {
        'name': fields.char('Description', size=64, ),
        'product_id': fields.many2one('product.product', 'Product', ),
        'partner_id': fields.many2one('res.partner', 'Vendor', required=True,),
        'company_id': fields.many2one('res.company', 'Company', required=True,),
        'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price')),
        'comment': fields.text('Additional Information'),
    }

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'partner.product.price', context=c),
    }



class res_partner(orm.Model):

    _inherit = "res.partner"


    _columns = {

        'product_price_ids': fields.one2many('partner.product.price', 'partner_id','Product Price for this Supplier', ),

    }

