# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Magnus NL (<http://magnus.nl>).
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

import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_invoice(osv.osv):
    """ Inherits invoice and adds state "verified" to supplier invoice workflow """
    _inherit = 'account.invoice'

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        if context is None:
            context = {}

        res = {}
        if context.get('verif_setting_change'):
            company_ids = context.get('company_ids', [])
            company_obj = self.pool['res.company'].browse(cr, uid, company_ids, context=context)
            for company in company_obj:
                treshold = company.verify_setting
                company_id = company.id

                cr.execute("""UPDATE account_invoice
                            SET verif_tresh_exceeded=True
                            WHERE amount_untaxed > %s
                            AND company_id= %s
                            AND type='in_invoice'
                            AND state!='paid';
                            UPDATE account_invoice
                            SET verif_tresh_exceeded=False
                            WHERE amount_untaxed <= %s
                            AND company_id= %s
                            AND type='in_invoice'
                            AND state!='paid'
                            """, ( treshold, company_id, treshold, company_id,))

        else:
            for invoice in self.browse(cr, uid, ids, context=context):
                res[invoice.id] = {
                    'amount_untaxed': 0.0,
                    'amount_tax': 0.0,
                    'amount_total': 0.0,
                    'verif_tresh_exceeded': None,
                }
                for line in invoice.invoice_line_ids:
                    res[invoice.id]['amount_untaxed'] += line.price_subtotal
                for line in invoice.tax_line_ids:
                    res[invoice.id]['amount_tax'] += line.amount

                res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
                if invoice.company_id.verify_setting < res[invoice.id]['amount_untaxed']:
                    res[invoice.id]['verif_tresh_exceeded'] = True
                else:
                    res[invoice.id]['verif_tresh_exceeded'] = False
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()



    def _setting_change(self, cr, uid, ids, context=None):
        # if context is None:
        #     context = {}
        context = dict(context or {})

        context['company_ids'] = ids
        context['verif_setting_change'] = True
        res = ids
        return res

    _columns = {
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),   
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('auth','Authorized'),
            ('verified','Verified'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True, track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
            \n* The \'Authorized\' status is used when invoice is already posted, but not yet confirmed for payment. \
            \n* The \'Verified\' status is used when invoice is already authorized, but not yet confirmed for payment, because it is of higher value than Company Verification treshold. \
            \n* The \'Open\' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice. \
            \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
            \n* The \'Cancelled\' status is used when user cancel invoice.'),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'verif_tresh_exceeded': fields.function(_amount_all,  type="boolean", string="Verification Treshold", track_visibility='always',
            store={
                'account.invoice':(lambda self, cr, uid, ids, c={}: ids,['invoice_line'], 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','quantity','discount','invoice_id'], 20),
                'res.company': (_setting_change, ['verify_setting'], 10),
            },
            multi='all'),

    }

