# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import osv, orm, fields
from openerp.tools.translate import _
from openerp import netsvc


class sale_order_line_create_multi_lines(orm.TransientModel):

    _name = "sale.order.line.create.multi.lines"
    _description = "Sale OrderLine Create Multi"


    def create_multi_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        #import pdb; pdb.set_trace()
        model = context.get('active_model', False)
        n = 0
        if model and model == 'sale.order':
            order_ids = context.get('active_ids', [])
            for so in self.pool['sale.order'].browse(cr, uid, order_ids, context):
                order_lines = [x.id for x in so.order_line]
                lines = self.pool['sale.order.line'].search(cr, uid, [('id', 'in', order_lines),
                                                                      ('adv_issue', '=', False)], context=context)
                if not lines:
                    continue
                n += 1
                olines = self.pool['sale.order.line'].browse(cr, uid, lines, context=context)
                self.create_multi_from_order_lines(cr, uid, olines, context)
            if n == 0:
                raise osv.except_osv(
                    _('Warning!'),
                    _('There are no Sales Order Lines without Advertising Issues in the selected Sales Orders.'))


        elif model and model == 'sale.order.line':
            orders = []
            line_ids = context.get('active_ids', [])
            for line in self.pool['sale.order.line'].browse(cr, uid, line_ids, context):
                if line.order_id.id not in orders:
                    orders.append(line.order_id.id)

            for oid in orders:
                lines = self.pool['sale.order.line'].search(cr, uid, [('order_id','=', oid),('id','in', line_ids),
                                                                      ('adv_issue','=', False)], context=context)
                if not lines:
                    continue
                n += 1
                olines = self.pool['sale.order.line'].browse(cr, uid, lines, context=context)
                self.create_multi_from_order_lines(cr, uid, olines, context)
            if n == 0:
                raise osv.except_osv(
                    _('Warning!'),
                    _('There are no Sales Order Lines without Advertising Issues in the selection.'))
        return

    def create_multi_from_order_lines(self, cr, uid, ids, context=None):

        sales_order_line_obj = self.pool['sale.order.line']
        for ol in ids:
            lines = [x.id for x in ol.order_id.order_line]
            number_ids = len([x.id for x in ol.adv_issue_ids])
            if number_ids < 1:
                raise osv.except_osv(
                    _('Error!'),
                    _('The product Quantity is different from the number of Issues in the multi line.'))
            uom_qty = ol.product_uom_qty / number_ids
            # uos_qty = ol.product_uos_qty / number_ids
            for ad_iss in ol.adv_issue_ids:
                res = {'adv_issue': ad_iss.id, 'adv_issue_ids': False, 'product_uom_qty': uom_qty,
                       # 'product_uos_qty': uos_qty,
                       'order_id': ol.order_id.id or False,
                       }
                vals = sales_order_line_obj.copy_data(cr, uid, ol.id, default=res, context=context)
                mol_id = sales_order_line_obj.create(cr, uid, vals, context=context)

                try: del context['__copy_data_seen']
                except: pass
                lines.append(mol_id)

            # TODO: FIXME
            # sales_order_line_obj.unlink(cr, uid, [ol.id])
            cr.execute("delete from sale_order_line where id = %s"%(ol.id))

        return



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
