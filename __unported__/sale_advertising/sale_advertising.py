# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2016 Magnus (<http://www.magnus.nl>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp
import time
from openerp.tools.translate import _

from openerp import api, fields as fields1, models, _



class sale_order(orm.Model):
    _inherit = "sale.order"


    def _amount_all(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}

        res = {}
        if context.get('verif_setting_change'):
            company_ids = context.get('company_ids', [])
            company_obj = self.pool['res.company'].browse(cr, uid, company_ids, context=context)
            for company in company_obj:
                treshold = company.verify_order_setting
                maxdiscount = company.verify_discount_setting
                company_id = company.id

                cr.execute("""UPDATE sale_order
                            SET ver_tr_exc=True
                            WHERE (amount_untaxed > %s
                            OR max_discount > %s)
                            AND company_id= %s
                            AND state!='done';
                            UPDATE sale_order
                            SET ver_tr_exc=False
                            WHERE amount_untaxed <= %s
                            AND company_id= %s
                            AND max_discount <= %s
                            AND state!='done'
                            """, ( treshold, maxdiscount, company_id,  treshold, company_id, maxdiscount ))

        else:
            cur_obj = self.pool.get('res.currency')
            for order in self.browse(cr, uid, ids, context=context):
                res[order.id] = {
                    'amount_untaxed': 0.0,
                    'amount_tax': 0.0,
                    'amount_total': 0.0,
                    'ver_tr_exc': None,
                }
                val = val1 = 0.0
                cdiscount = []
                cur = order.pricelist_id.currency_id
                for line in order.order_line:
                    cdiscount.append(line.computed_discount)
                    val1 += line.price_subtotal
                    val += self._amount_line_tax(cr, uid, line, context=context)
                if cdiscount:
                    max_cdiscount = max(cdiscount)
                else: max_cdiscount = 0.0
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
                res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
                res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
                if order.company_id.verify_order_setting < res[order.id]['amount_untaxed'] or order.company_id.verify_discount_setting < max_cdiscount:
                    res[order.id]['ver_tr_exc'] = True
                else:
                    res[order.id]['ver_tr_exc'] = False
        return res

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        print "line.tax_id", line.tax_id
        # for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.actual_unit_price * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.product_id, line.order_id.partner_id)['taxes']:
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id.id, price_unit=line.actual_unit_price * (1-(line.discount or 0.0)/100.0),
                                                          quantity=line.product_uom_qty, product_id=line.product_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    def _get_order(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('sale.order.line')
        return list(set(line['order_id'] for line in line_obj.read(
            cr, uid, ids, ['order_id'], load='_classic_write', context=context)))

    def _setting_change(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context['company_ids'] = ids
        context['verif_setting_change'] = True
        res = ids
        return res

    _columns = {
        'published_customer': fields.many2one('res.partner', 'Advertiser', domain=[('customer','=',True)]),
        'advertising_agency': fields.many2one('res.partner', 'Advertising Agency', domain=[('customer','=',True)]),
        'nett_nett': fields.boolean('Netto Netto Deal', ),
        'customer_contact': fields.many2one('res.partner', 'Payer Contact Person', domain=[('customer','=',True)]),
        'traffic_employee': fields.many2one('res.users', 'Traffic Employee',),
        'traffic_comments': fields.text('Traffic Comments'),
        'traffic_appr_date': fields.date('Traffic Confirmation Date', select=True, help="Date on which sales order is confirmed bij Traffic."),
        'opportunity_subject': fields.char('Opportunity Subject', size=64,
                              help="Subject of Opportunity from which this Sales Order is derived."),
        'partner_acc_mgr': fields.related('published_customer', 'user_id', type='many2one', relation='res.users', string='Account Manager', store=True , readonly=True),
        'date_from': fields.function(lambda *a, **k: {}, method=True, type='date', string="Date from"),
        'date_to': fields.function(lambda *a, **k: {}, method=True, type='date', string="Date to"),
        # 'state': fields.selection([
        #     ('draft', 'Draft Quotation'),
        #     ('submitted', 'Submitted for Approval'),
        #     ('approved1', 'Approved by Sales Mgr'),
        #     ('approved2', 'Approved by Traffic'),
        #     ('sent', 'Quotation Sent'),
        #     ('cancel', 'Cancelled'),
        #     ('waiting_date', 'Waiting Schedule'),
        #     ('progress', 'Sales Order'),
        #     ('manual', 'Sale to Invoice'),
        #     ('invoice_except', 'Invoice Exception'),
        #     ('done', 'Done'),
        # ], 'Status', readonly=True, track_visibility='onchange',
        #     help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a "
        #          "cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' "
        #          "status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.",
        #     select=True),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                       'sale.order.line':(_get_order, ['actual_unit_price', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                       'sale.order.line':(_get_order, ['actual_unit_price', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                       'sale.order.line':(_get_order, ['actual_unit_price', 'tax_id', 'discount', 'product_uom_qty'], 10),
                                        },
                                multi='sums', help="The total amount."),
        'ver_tr_exc': fields.function(_amount_all, type="boolean", string="Verification Treshold",track_visibility='always',
                                store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                                       'sale.order.line':(_get_order, ['actual_unit_price', 'discount', 'product_uom_qty'], 20),
                                       'res.company':(_setting_change, ['verify_order_setting', 'verify_discount_setting'], 10),
                                        },
                                multi='sums'),

    }
    _defaults = {
        'nett_nett': False,
    }

    # rewritten below:
    # def onchange_published_customer(self, cr, uid, ids, published_customer, context):
    #     data = {'partner_id':published_customer, 'partner_invoice_id': False,
    #             'partner_shipping_id':False, 'partner_order_id':False, 'advertising_agency': False}
    #     if published_customer:
    #         address = self.onchange_partner_id(cr, uid, ids, published_customer, context)
    #         data.update(address['value'])
    #     return {'value' : data }

    # rewritten below:
    # def onchange_advertising_agency(self, cr, uid, ids, ad_agency, context):
    #     if ad_agency:
    #         data = {'partner_id': ad_agency, 'partner_invoice_id': False, 'partner_shipping_id': False,
    #                 'partner_order_id': False}
    #         address = self.onchange_partner_id(cr, uid, ids, ad_agency, context)
    #         data.update(address['value'])
    #         return {'value' : data}
    #     return True

    def action_submit(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot submit a quotation/sales order which has no line.'))
        # return True
        return self.write(cr, uid, ids, {'state':'submitted'})

    def action_approve2(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id],
                       {'state': 'approved2', 'traffic_appr_date': fields.date.context_today(self, cr, uid, context=context)})
        return True

    # rewritten below:
    # def onchange_partner_id2(self, cr, uid, ids, part, lines, context=None):
    #     res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
    #     if not part:
    #         return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'customer_contact': False, 'payment_term': False, 'fiscal_position': False}}
    #     part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
    #     addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
    #     if part.type == 'contact':
    #         contact = self.pool['res.partner'].search(cr, uid, [('is_company','=', False),('type','=', 'contact'),('parent_id','=', part.id)], context=context)
    #         if len(contact) >=1:
    #             contact_id = contact[0]
    #         else:
    #             contact_id = False
    #     elif addr['contact'] == addr['default']:
    #         contact_id = False
    #     else: contact_id = addr['contact']
    #
    #     result = {}
    #     if lines:
    #         result['warning'] = {'title':_('Warning'),
    #                              'message':_('Changing the Customer can have a change in Agency Discount as a result.'
    #                                          'This change will only show after saving the order!'
    #                                          'Before saving the order the order lines and the total amounts may therefor'
    #                                          'show wrong values.')}
    #         res.update(result)
    #     res['value']['user_id'] = uid
    #     res['value']['customer_contact'] = contact_id
    #     return res

    def update_line_discount(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        order = self.browse(cr, uid, ids[0], context=context)
        discount = order.partner_id.agency_discount or 0.0
        if order.nett_nett:
            discount = 0.0
        fiscal_position = order.partner_id.property_account_position_id.id
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        line_ids = self.pool['sale.order.line'].search(cr, uid, [('order_id', 'in', ids)], context=context)
        if line_ids:
            for line in self.pool['sale.order.line'].browse(cr, uid, line_ids):
                product = self.pool['product.product'].browse(cr, uid, line.product_id.id)
                tax = self.pool['account.fiscal.position'].map_tax(cr, uid, fpos, product.taxes_id)
                vals = {}
                vals['discount'] = discount
                vals['tax_id'] = [(6,0,tax)]

                self.pool['sale.order.line'].write(cr, uid, line.id, vals, context=context)

        return True

    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order, self).write(
            cr, uid, ids, vals, context=context)
        if 'partner_id' in vals or 'nett_nett' in vals:
            self.update_line_discount(cr, uid, ids, context=context)
        return res

    def create(self, cr, uid, vals, context=None):
        res = super(sale_order, self).create(
            cr, uid, vals, context=context)
        self.update_line_discount(cr, uid, [res], context=context)
        return res



class sale_advertising_issue(orm.Model):
    _name = "sale.advertising.issue"
    _inherits = {
        'account.analytic.account': 'analytic_account_id',
    }
    _description="Sale Advertising Issue"


    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'child_ids': fields.one2many('sale.advertising.issue', 'parent_id', 'Issues',),
        'parent_id': fields.many2one('sale.advertising.issue', 'Title', select=True),
        'analytic_account_id': fields.many2one('account.analytic.account', required=True,
                                      string='Related Analytic Account', ondelete='restrict',
                                      help='Analytic-related data of the issue'),
        'issue_date': fields.related('analytic_account_id','date_publish', type='date', string='Issue Date',),
        'medium': fields.many2one('product.category','Medium', required=True),
        'state': fields.selection([('open','Open'),('close','Close')], 'State'),
        'default_note': fields.text('Default Note'),
    }

    _defaults = {
        'state': 'open',
    }




class sale_order_line(orm.Model):
    _inherit = "sale.order.line"

    # rewritten below
    # def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
    #     tax_obj = self.pool.get('account.tax')
    #     cur_obj = self.pool.get('res.currency')
    #     res = {}
    #
    #     if context is None:
    #         context = {}
    #     for line in self.browse(cr, uid, ids, context=context):
    #         comp_discount = 0.0
    #         res[line.id] = {
    #             'price_unit': 0.0,
    #             'computed_discount': 0.0,
    #             'price_subtotal': 0.0,
    #         }
    #         if not line.order_id.date_order:
    #             date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
    #         else: date_order = line.order_id.date_order
    #         pricelist = line.order_id.pricelist_id and line.order_id.pricelist_id.id or False
    #         product_id = line.product_id and line.product_id.id or False
    #         order_partner_id = line.order_id.partner_id and line.order_id.partner_id.id or False
    #         discount = line.discount or 0.0
    #         if line.order_id.nett_nett:
    #             discount = 0.0
    #         product_uom = line.product_uom and line.product_uom.id or False
    #         if product_id:
    #             unit_price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], product_id,
    #                                                     line.product_uom_qty or 1.0, order_partner_id,
    #                                                 {'uom': product_uom, 'date': date_order,})[pricelist]
    #         else: unit_price = 0.0
    #         if unit_price > 0.0:
    #             comp_discount = (unit_price - line.actual_unit_price)/unit_price * 100.0
    #         price = line.actual_unit_price * (1 - discount / 100.0)
    #         subtotal_bad = line.actual_unit_price * line.product_uom_qty
    #         taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, order_partner_id)
    #         cur = line.order_id.pricelist_id.currency_id
    #         res[line.id]['price_unit'] = unit_price
    #         res[line.id]['computed_discount'] = comp_discount
    #         res[line.id]['subtotal_before_agency_disc'] = subtotal_bad
    #         res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
    #     return res


    _columns = {
        'layout_remark': fields.text('Layout Remark'),
        'title': fields.many2one('sale.advertising.issue', 'Title', domain=[('child_ids','=', True)]),
        'adv_issue_ids': fields.many2many('sale.advertising.issue','sale_order_line_adv_issue_rel', 'order_line_id',
                                          'adv_issue_id',  'Advertising Issues'),
        'dates': fields.one2many('sale.order.line.date', 'order_line_id', 'Advertising Dates'),
        'dateperiods': fields.one2many('sale.order.line.dateperiod', 'order_line_id', 'Advertising Date Periods'),
        'date_type': fields.related('ad_class', 'date_type', type='selection',
                       selection=[
                            ('validity', 'Validity Date Range'),
                            ('date', 'Date of Publication'),
                            ('newsletter', 'Newsletter'),
                            ('online', 'Online'),
                            ('issue_date', 'Issue Date'),
                       ], relation='product.category', string='Date Type', readonly=True),
        'adv_issue': fields.many2one('sale.advertising.issue','Advertising Issue'),
        'medium': fields.related('title', 'medium', type='many2one', relation='product.category',string='Medium', readonly=True ),
        'ad_class': fields.many2one('product.category', 'Advertising Class'),
        'page_reference': fields.char('Reference of the Page', size=32),
        'ad_number': fields.char('Advertising Reference', size=32),
        'from_date': fields.date('Start of Validity'),
        'to_date': fields.date('End of Validity'),
        'order_partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', string='Customer'),
        'discount_dummy': fields.related('discount', type='float', string='Agency Commission (%)',readonly=True ),
        'actual_unit_price' :fields.float('Actual Unit Price', required=True, digits_compute=dp.get_precision('Actual Unit Price'), readonly=True, states={'draft': [('readonly', False)]}),

        # 'price_unit': fields.function(_amount_line, string='Unit Price', type='float', digits_compute=dp.get_precision('Product Price'), multi=True),
        # 'computed_discount' :fields.function(_amount_line, string='Discount (%)', digits_compute=dp.get_precision('Account'), type="float", multi=True),
        # 'subtotal_before_agency_disc': fields.function(_amount_line, string='Subtotal before Commission', digits_compute=dp.get_precision('Account'), type="float", multi=True),
        # 'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account'), type="float", multi=True),
    }

    _defaults = {
        'actual_unit_price': 0.0,
        'computed_discount': 0.0,
        'product_uom_qty': 0.0
    }



    def onchange_title(self, cr, uid, ids, title=False, context=None):
        if context is None:
            context = {}
        data = {}
        vals = {}
        if title:
            ad_issue_obj = self.pool['sale.advertising.issue']
            ad_issue = ad_issue_obj.browse(cr, uid, title, context=context)
            child_id = [x.id for x in ad_issue.child_ids]
            if len(child_id) == 1:
                vals['adv_issue'] = child_id
                vals['adv_issue_ids'] = [(6,0,[])]
                vals['ad_class'] = False
                vals['product_id'] = False
                #vals['actual_unit_price'] = 0.0
                ac = ad_issue.medium and ad_issue.medium.id or False
                vals['medium'] = ac
                data = {'ad_class': [('id', 'child_of', ac), ('type', '!=', 'view')]}
                ac_child = self.pool['product.category'].search(cr, uid,
                                                                [('id', 'child_of', ac), ('type', '!=', 'view')],
                                                                context)
                if len(ac_child) == 1:
                    vals['ad_class'] = ac_child[0]


            else:
                vals['adv_issue'] = False
                vals['ad_class'] = False
                vals['product_id'] = False
                #vals['actual_unit_price'] = 0.0
                ac = ad_issue.medium and ad_issue.medium.id or False
                vals['medium'] = ac
                data = {'ad_class': [('id', 'child_of', ac), ('type', '!=', 'view')]}
                ac_child = self.pool['product.category'].search(cr, uid,
                                                                [('id', 'child_of', ac), ('type', '!=', 'view')],
                                                                context)
                if len(ac_child) == 1:
                    vals['ad_class'] = ac_child[0]

        return {'value': vals, 'domain': data}

    # rewitten below
    # def onchange_adv_issue_ids(self, cr, uid, ids, adv_issue_id=False, adv_issue_ids=False, context=None):
    #     if context is None:
    #         context = {}
    #     vals = {}
    #     if not adv_issue_id and adv_issue_ids:
    #         if len(adv_issue_ids[0][2]) >= 1:
    #             qty = len(adv_issue_ids[0][2])
    #         else:
    #             qty = 0
    #     elif adv_issue_id:
    #         qty = 1
    #
    #     vals['product_uom_qty'] = qty
    #     return {'value': vals}


    def onchange_ad_class(self, cr, uid, ids, ad_class=False, context=None):
        if context is None:
            context = {}
        vals = {}
        data = {}
        result = {}
        if ad_class:
            product_ids = self.pool.get('product.product').search(cr, uid, [('categ_id', '=', ad_class)], context=context )
            if product_ids:
                data['product_id'] = [('categ_id', '=', ad_class)]
                if len(product_ids) == 1:
                    vals['product_id'] = product_ids[0]
                else:
                    vals['product_id'] = False
            a_c = self.pool.get('product.category').browse(cr, uid, ad_class, context=context )
            date_type = a_c.date_type or False
            if date_type:
                vals['date_type'] = date_type
            else: result = {'title':_('Warning'),
                                 'message':_('The Ad Class has no Date Type. You have to define one')}
        else:
            vals['product_id'] = False
            vals['date_type'] = False
        return {'value': vals, 'domain' : data, 'warning': result}

    def onchange_date_type(self, cr, uid, ids, date_type=False, dates=False, dateperiods=False, adv_issue_ids=False, context=None):
        if context is None:
            context = {}
        vals = {}

        if date_type:
            if date_type == 'date':
                if dateperiods:
                    vals['dateperiods'] = [(6,0,[])] #[(2,x[1]) for x in dateperiods]
                if adv_issue_ids:
                    vals['adv_issue_ids'] = [(6,0,[])]
            elif date_type == 'validity':
                if dates:
                    vals['dates'] = [(6,0,[])] #[(2, x[1]) for x in dates]
                if adv_issue_ids:
                    vals['adv_issue_ids'] = [(6,0,[])]
            elif date_type == 'issue_date':
                if dates:
                    vals['dates'] = [(6,0,[])] #[(2, x[1]) for x in dates]
                if dateperiods:
                    vals['dateperiods'] = [(6,0,[])] #[(2, x[1]) for x in dateperiods]
        return {'value': vals}


    # # rewritten below
    # def onchange_dates(self, cr, uid, ids, dates=False, context=None):
    #     if context is None:
    #         context = {}
    #     vals = {}
    #     if dates:
    #         if len(dates) >= 1:
    #             qty = len(dates)
    #         else:
    #             qty = 0
    #     else:
    #         qty = 0
    #
    #     vals['product_uom_qty'] = qty
    #     return {'value': vals}


    def onchange_actualup(self, cr, uid, ids, actual_unit_price=False, price_unit=False, qty=0.0, discount=False, context=None):
        result = {}
        if context is None:
            context = {}
        if actual_unit_price and actual_unit_price > 0.0:
            if price_unit and price_unit > 0.0:
                cdisc = (float(price_unit) - float(actual_unit_price)) / float(price_unit) * 100.0
                result['computed_discount'] = cdisc
                result['subtotal_before_agency_disc'] = round((float(actual_unit_price) * float(qty)), 2)
                result['price_subtotal'] = round((float(actual_unit_price) * float(qty) * (1.0 - float(discount)/100.0)), 2)
            else:
                result['computed_discount'] = 0.0
                result['subtotal_before_agency_disc'] = round((float(actual_unit_price) * float(qty)), 2)
                result['price_subtotal'] = round((float(actual_unit_price) * float(qty) * (1.0 - float(discount)/100.0)), 2)
        else:
            if price_unit and price_unit > 0.0:
                result['actual_unit_price'] = 0.0
            result['computed_discount'] = 100.0
            result['subtotal_before_agency_disc'] = round((float(actual_unit_price) * float(qty)), 2)
            result['price_subtotal'] = round((float(actual_unit_price) * float(qty) * (1.0 - float(discount)/100.0)), 2)
        return {'value': result}

    def onchange_price_subtotal(self,cr, uid, ids, discount=0.0, qty=0, subtotal_before_agency_disc=0.0, context=None):
        result = {}
        if context is None:
            context = {}
        if subtotal_before_agency_disc and subtotal_before_agency_disc > 0.0:
                if qty > 0.0:
                    actual_unit_price = float(subtotal_before_agency_disc) / float(qty)
                    result['actual_unit_price'] = actual_unit_price
                    result['price_subtotal'] = round((float(subtotal_before_agency_disc) * (1.0 - float(discount) / 100.0)), 2)
        else:
            result['actual_unit_price'] = 0.0
            result['price_subtotal'] = 0.0
        return {'value': result}

    def onchange_price_unit(self, cr, uid, ids, price_unit=0.0, context=None):
        if context is None:
            context = {}
        vals = {}
        if price_unit > 0.0:
            vals['actual_unit_price'] = price_unit
        return {'value': vals}

    # # rewritten below
    # def qty_change(self, cr, uid, ids, actual_unit_price=0.0, price_unit=0.0, pricelist=False, product=False, qty=0, uom=False, qty_uos=0, uos=False, name='',
    #         partner_id=False, lang=False, update_tax=True, date_order=False, adv_issue_ids=False, dates=False, date_type=False,
    #         packaging=False, nett_nett=False, fiscal_position=False, flag=False, context=None):
    #     res = self.product_id_change(cr, uid, ids, pricelist=pricelist, product=product, qty=qty, uom=uom,
    #                                  qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id, lang=lang,
    #                                  update_tax=update_tax, date_order=date_order,
    #                                  packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
    #     mqty = False
    #     if date_type == 'issue_date' and adv_issue_ids:
    #         if len(adv_issue_ids[0][2]) >= 1:
    #             mqty = len(adv_issue_ids[0][2])
    #         else:
    #             mqty = 0
    #
    #     if date_type == 'date' and dates:
    #         if len(dates) >= 1:
    #             mqty = len(dates)
    #         else:
    #             mqty = 0
    #     if mqty:
    #         qty = mqty
    #         res['value']['product_uom_qty'] = qty
    #     partner = self.pool['res.partner'].browse(cr, uid, partner_id, context=context)
    #     if partner.is_ad_agency and not nett_nett:
    #         discount = partner.agency_discount
    #     else:
    #         discount = 0.0
    #     res['value'].update({'discount': discount, 'discount_dummy': discount})
    #     if 'price_unit' in res['value']:
    #         pu = res['value']['price_unit']
    #         if pu != price_unit:
    #             actual_unit_price = pu
    #     else:
    #         pu = 0.0
    #     res2 = self.onchange_actualup(cr, uid, ids, actual_unit_price=actual_unit_price, price_unit=pu, qty=qty,
    #                                   discount=discount, context=context)
    #     res['value'].update(res2['value'])
    #     return res


    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = super(sale_order_line,self)._prepare_order_line_invoice_line(cr, uid, line, account_id=account_id, context=context)
        res['account_analytic_id'] = line.adv_issue.analytic_account_id and line.adv_issue.analytic_account_id.id or False
        return res

class sale_order_line_date(orm.Model):

    _name = "sale.order.line.date"
    _description= "Advertising Order Line Dates"
    _order = "order_line_id,sequence,id"

    _columns = {
        'sequence': fields.integer('Sequence', help="Gives the sequence of this line ."),
        'order_line_id': fields.many2one('sale.order.line', 'Line', ondelete='cascade', select=True, required=True),
        'issue_date': fields.date('Date of Issue'),
        'name': fields.char('Name', size=64),
        'page_reference': fields.char('Reference of the Page', size=32),
        'ad_number': fields.char('Advertising Reference', size=32),

    }
    _defaults = {
        #'type': 'date',
        'sequence': 10,
    }

class sale_order_line_dateperiod(orm.Model):

    _name = "sale.order.line.dateperiod"
    _description= "Advertising Order Line Date Periods"
    _order = "order_line_id,sequence,id"

    _columns = {
        'sequence': fields.integer('Sequence', help="Gives the sequence of this line ."),
        'order_line_id': fields.many2one('sale.order.line', 'Line', ondelete='cascade', select=True, required=True),
        'from_date': fields.date('Start of Validity'),
        'to_date': fields.date('End of Validity'),
        'name': fields.char('Name', size=64),
        'page_reference': fields.char('Reference of the Page', size=32),
        'ad_number': fields.char('Advertising Reference', size=32),

    }
    _defaults = {
        #'type': 'date',
        'sequence': 10,
    }


class sale_advertising_proof(orm.Model):
    _name = "sale.advertising.proof"
    _description="Sale Advertising Proof"
    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'address_id':fields.many2one('res.partner','Delivery Address', required=True),
        'number': fields.integer('Number of Copies', required=True),
        'target_id': fields.many2one('sale.order','Target', required=True),
    }
    _defaults = {
        'number': 1,
    }



class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields1.Selection([
        ('draft', 'Quotation'),
        ('submitted', 'Submitted for Approval'),
        ('approved1', 'Approved by Sales Mgr'),
        ('approved2', 'Approved by Traffic'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sale Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


    # overridden:
    @api.multi
    @api.onchange('partner_id', 'published_customer', 'advertising_agency')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        if self.published_customer:
            self.partner_id = self.published_customer.id

        if self.advertising_agency:
            self.partner_id = self.advertising_agency

        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
                'customer_contact': False
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        if self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.user_id:
            values['user_id'] = self.partner_id.user_id.id
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

        if self.partner_id.type == 'contact':
            contact = self.env['res.partner'].search([('is_company','=', False),('type','=', 'contact'),('parent_id','=', self.partner_id.id)])
            if len(contact) >=1:
                contact_id = contact[0]
            else:
                contact_id = False
        elif addr['contact'] == addr['default']:
            contact_id = False
        else: contact_id = addr['contact']

        if self.order_line:
            warning = {'title':_('Warning'),
                                 'message':_('Changing the Customer can have a change in Agency Discount as a result.'
                                             'This change will only show after saving the order!'
                                             'Before saving the order the order lines and the total amounts may therefor'
                                             'show wrong values.')}
            return {'warning': warning}
        values['user_id'] = self._uid
        values['customer_contact'] = contact_id
        self.update(values)

    # --added deep
    @api.multi
    def action_approve1(self):
        self.action_submit()
        return self.write({'state':'approved1'})

    # --added deep
    @api.multi
    def action_refuse(self):
        self.action_submit()
        return self.write({'state':'draft'})

    # overridden: -- added deep
    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'approved2').write({'state': 'sent'})
        return self.env['report'].get_action(self, 'sale.report_saleorder')



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:

            if not line.order_id.date_order:
                date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
            else: date_order = line.order_id.date_order

            pricelist = line.order_id.pricelist_id and line.order_id.pricelist_id.id or False
            product_id = line.product_id and line.product_id.id or False
            order_partner_id = line.order_id.partner_id and line.order_id.partner_id.id or False
            discount = line.discount or 0.0
            comp_discount = 0.00

            if line.order_id.nett_nett:
                discount = 0.0
            product_uom = line.product_uom and line.product_uom.id or False

            if product_id:
                unit_price = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [pricelist],
                            product_id, line.product_uom_qty or 1.0, order_partner_id, context={'uom': product_uom, 'date': date_order,})[pricelist]


            else: unit_price = 0.0
            if unit_price > 0.0:
                comp_discount = (unit_price - line.actual_unit_price)/unit_price * 100.0

            price = line.actual_unit_price * (1 - discount / 100.0)
            subtotal_bad = line.actual_unit_price * line.product_uom_qty
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)

            line.update({
                'price_unit': unit_price,
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'computed_discount': comp_discount,
                'subtotal_before_agency_disc': subtotal_bad

            })


    price_unit = fields1.Monetary(compute='_compute_amount', string='Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0, store=True)
    price_subtotal = fields1.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)

    computed_discount = fields1.Monetary(compute='_compute_amount', string='Discount (%)', digits_compute=dp.get_precision('Account'), store=True)
    subtotal_before_agency_disc = fields1.Monetary(compute='_compute_amount', string='Subtotal before Commission', digits_compute=dp.get_precision('Account'), store=True)

    @api.onchange('adv_issue', 'adv_issue_ids')
    def onchange_adv_issue_ids(self):
        qty = 0.00

        if not self.adv_issue and self.adv_issue_ids:
            if len(self.adv_issue_ids) >= 1:
                qty = len(self.adv_issue_ids)
            else:
                qty = 0
        elif self.adv_issue:
            qty = 1

        self.product_uom_qty = qty


    @api.onchange('dates')
    def onchange_dates(self):
        vals = {}
        if self.dates:
            if len(self.dates) >= 1:
                qty = len(self.dates)
            else:
                qty = 0
        else:
            qty = 0

        self.product_uom_qty = qty


    @api.onchange('product_uom_qty')
    def qty_change(self):
        res = self.product_id_change()

        mqty = False
        if self.date_type == 'issue_date' and self.adv_issue_ids:
            if len(self.adv_issue_ids) >= 1:
                mqty = len(self.adv_issue_ids)
            else:
                mqty = 0

        if self.date_type == 'date' and self.dates:
            if len(self.dates) >= 1:
                mqty = len(self.dates)
            else:
                mqty = 0
        if mqty:
            qty = mqty
            self.product_uom_qty = qty

        partner = self.order_id.partner_id
        if partner.is_ad_agency and not self.order_id.nett_nett:
            discount = partner.agency_discount
        else:
            discount = 0.0
        self.update({'discount': discount, 'discount_dummy': discount})

        # TODO: FIXME
        # if self.price_unit:
        #     pu = self.price_unit
        #     if pu != self.price_unit:
        #         actual_unit_price = pu
        # else:
        #     pu = 0.0
        res2 = self.onchange_actualup()
        self.update(res2['value'])
        return res


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'sale.order' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            order = self.env['sale.order'].browse([self._context['default_res_id']])
            if order.state == 'approved2':
                order.state = 'sent'
        return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(auto_commit=auto_commit)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

