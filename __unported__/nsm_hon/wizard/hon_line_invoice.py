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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc
import time

class hon_issue_make_invoice(osv.osv_memory):
    _name = "hon.issue.make.invoice"
    _description = "Honorarium Issue Make_invoice"

    def make_invoices_from_issues(self, cr, uid, ids, context=None):
        issue_ids = context.get('active_ids', [])
        his_obj = self.pool.get('hon.issue.line.make.invoice')
        lines = self.pool['hon.issue.line'].search(cr, uid, [('issue_id','in', [issue_ids])], context=context)
        context['active_ids'] = lines
        his_obj.make_invoices_from_lines(cr, uid, lines, context=context)
        return True

class hon_issue_line_make_invoice(osv.osv_memory):
    _name = "hon.issue.line.make.invoice"
    _description = "Honorarium Issue Line Make_invoice"

    def _prepare_invoice(self, cr, uid, partner, issue, category, lines, context=None):
        issue_invoices = self.pool['hon.issue'].browse(cr, uid, issue.id, context=context)
        invoices = self.pool['account.invoice'].search(cr, uid, [('id','in', [x.id for x in issue_invoices.invoice_ids]),('partner_id','=',partner.id)], context=context)
        if len(invoices) >= 1:
            inv_count = len(invoices) + 1
        else:
            inv_count = 1
        a = partner.property_account_payable_id.id
        if partner and partner.property_supplier_payment_term_id.id:
            pay_term = partner.property_supplier_payment_term_id.id
        else:
            pay_term = False

        # -- deep: validation added
        HonJournalID = issue.company_id.hon_journal and issue.company_id.hon_journal.id or False
        if not HonJournalID:
            raise osv.except_osv(_('Warning!'), _('Please map "Honorarium Journal" in the Company master.'))

        return {
            'name': lines['name'] or '',
            'hon': True,
            'origin': issue.account_analytic_id.name,
            'type': 'in_invoice',
            'reference': False,
            'date_publish': issue.date_publish,
            'account_id': a,
            'partner_id': partner.id,
            'invoice_line_ids': [(6, 0, lines['lines'])],
            'comment': issue.comment,
            'payment_term': pay_term,
            # 'journal_id': issue.company_id.hon_journal and issue.company_id.hon_journal.id or False,
            'journal_id': HonJournalID,

            'fiscal_position': partner.property_account_position_id.id,
            'supplier_invoice_number': "HON%dNo%d" % (issue.id, inv_count),

            # TODO: FIXME
            # Migration fixes: section_ids no longer exists in Analytic
            # 'section_id': issue.account_analytic_id.section_ids[0] and issue.account_analytic_id.section_ids[0].id or False,

            'user_id': uid,
            'company_id': issue.company_id and issue.company_id.id or False,
            'date_invoice': context.get('date_invoice', []) or fields.date.today(),
            'partner_bank_id': partner.bank_ids and partner.bank_ids[0].id or False,
            'product_category': category.id,
            'check_total': lines['subtotal'],
            # 'main_account_analytic_id': issue.account_analytic_id.parent_id.id
        }

    
    def make_invoices_from_lines(self, cr, uid, ids, context=None):
        """
             To make invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        if context is None: context = {}
        if not context.get('active_ids', []):
            raise osv.except_osv(_('Warning!'), _(
                'No Issue lines are selected for invoicing:\n'))
        else: lids = context.get('active_ids', [])
        res = False
        invoices = {}

        def make_invoice(partner, issue, category, lines, context=context):
            """
                 To make invoices.

                 @param issue:
                 @param lines:

                 @return:

            """
            inv = self._prepare_invoice(cr, uid, partner, issue, category, lines, context=context)
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv)
            cr.execute('insert into hon_issue_invoice_rel (issue_id,invoice_id) values (%s,%s)', (issue.id, inv_id))
            return inv_id

        hon_issue_line_obj = self.pool.get('hon.issue.line')
        hon_issue_obj = self.pool.get('hon.issue')
        wf_service = netsvc.LocalService('workflow')

        for line in hon_issue_line_obj.browse(cr, uid, lids, context=context):
            if (not line.invoice_line_id) and (line.state not in ('draft', 'cancel')) and (not line.employee) and (not line.gratis):
                if not (line.issue_id.id, line.partner_id.id, line.product_category_id.id) in invoices:
                    invoices[(line.issue_id.id, line.partner_id.id, line.product_category_id.id)] = {'lines':[],'subtotal':0, 'name': ''}
                inv_line_id = hon_issue_line_obj.invoice_line_create(cr, uid, [line.id])
                for lid in inv_line_id:
                    invoices[(line.issue_id.id, line.partner_id.id, line.product_category_id.id)]['lines'].append(lid)
                    invoices[(line.issue_id.id, line.partner_id.id, line.product_category_id.id)]['subtotal'] += line.price_subtotal
                    invoices[(line.issue_id.id, line.partner_id.id, line.product_category_id.id)]['name'] += str(line.name)+' / '

        if not invoices:
            raise osv.except_osv(_('Warning!'), _('Invoice cannot be created for this Honorarium Issue Line due to one of the following reasons:\n'
                                                  '1.The state of this hon issue line is either "draft" or "cancel"!\n'
                                                  '2.The Honorarium Issue Line is Invoiced!\n'
                                                  '3.The Honorarium Issue Line is marked "gratis"\n'
                                                  '4.The Honorarium Issue Line has an Employee as Creditor\n'))

        for issue_partner_category, il in invoices.items():
            issue_id = issue_partner_category[0]
            partner_id = issue_partner_category[1]
            category_id = issue_partner_category[2]
            issue = hon_issue_obj.browse(cr, uid, issue_id, context=context)
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            category = self.pool.get('product.category').browse(cr, uid, category_id, context=context)
            res = make_invoice(partner, issue, category, il,)

        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, res, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def open_invoices(self, cr, uid, invoice_ids, context=None):
        """ open a view on one of the given invoice_ids """
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Invoice'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'account.invoice',
            'res_id': invoice_ids,
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'context': {'type': 'in_invoice'},
            'type': 'ir.actions.act_window',
        }

hon_issue_line_make_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
