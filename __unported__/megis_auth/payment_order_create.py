# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009 EduSense BV (<http://www.edusense.nl>).
#              (C) 2011 - 2013 Therp BV (<http://therp.nl>).
#              (C) 2013 Eurogroup Consulting BV (http://www.eurogroupconsulting.nl)    
#            
#    All other contributions are (C) by their respective contributors
#
#    All Rights Reserved
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
#############################################################################

# from openerp.osv import orm, fields
# from openerp.tools.translate import _

from openerp import models, fields, api, _

# class payment_order_create(orm.TransientModel):
#     _inherit = 'payment.order.create'
#
# #    def extend_payment_order_domain(
# #            self, cr, uid, payment_order, domain, context=None):
# #        if payment_order.payment_order_type == 'payment':
# #            domain += [
# #                ('account_id.type', '=', 'payable'),
# #                ('amount_to_pay', '>', 0)
# #                ('invoice.state', '=', 'auth')
# #                ]
# #        return True
#
#     def search_entries(self, cr, uid, ids, context=None):
#         """
#         This method taken from account_banking_payment module.
#         We adapt the domain based on the invoice status (must be 'auth')
#         """
#         line_obj = self.pool.get('account.move.line')
#         mod_obj = self.pool.get('ir.model.data')
#         if context is None:
#             context = {}
#         data = self.read(cr, uid, ids, ['duedate'], context=context)[0]
#         search_due_date = data['duedate']
#
#         ### start account_banking_payment ###
#         payment = self.pool.get('payment.order').browse(
#             cr, uid, context['active_id'], context=context)
#         # Search for move line to pay:
#         domain = [
#             ('move_id.state', '=', 'posted'),
#             ('reconcile_id', '=', False),
#             ('company_id', '=', payment.mode.company_id.id),
#             ('invoice.state', '=', 'auth'),
#             ]
#
#         # apply payment term filter
#         if payment.mode.payment_term_ids:
#             domain += [
#                 ('invoice.payment_term', 'in',
#                  [term.id for term in payment.mode.payment_term_ids]
#                  )
#                 ]
#         self.extend_payment_order_domain(
#             cr, uid, payment, domain, context=context)
#         ### end account_direct_debit ###
#
#         domain = domain + [
#             '|', ('date_maturity', '<=', search_due_date),
#             ('date_maturity', '=', False)
#             ]
#         line_ids = line_obj.search(cr, uid, domain, context=context)
#         context.update({'line_ids': line_ids})
#         model_data_ids = mod_obj.search(
#             cr, uid,[
#                 ('model', '=', 'ir.ui.view'),
#                 ('name', '=', 'view_create_payment_order_lines')],
#             context=context)
#         resource_id = mod_obj.read(
#             cr, uid, model_data_ids, fields=['res_id'],
#             context=context)[0]['res_id']
#         return {'name': _('Entry Lines'),
#                 'context': context,
#                 'view_type': 'form',
#                 'view_mode': 'form',
#                 'res_model': 'payment.order.create',
#                 'views': [(resource_id, 'form')],
#                 'type': 'ir.actions.act_window',
#                 'target': 'new',
#         }


class AccountPaymentLineCreate(models.TransientModel):
    _inherit = 'account.payment.line.create'


    # Overridden:
    @api.multi
    def _prepare_move_line_domain(self):
        self.ensure_one()
        journals = self.journal_ids or self.env['account.journal'].search([])
        domain = [('reconciled', '=', False),
                  ('company_id', '=', self.order_id.company_id.id),
                  ('journal_id', 'in', journals.ids),
                  ('invoice_id.state', '=', 'auth')]

        if self.target_move == 'posted':
            domain += [('move_id.state', '=', 'posted')]
        if not self.allow_blocked:
            domain += [('blocked', '!=', True)]
        if self.date_type == 'due':
            domain += [
                '|',
                ('date_maturity', '<=', self.due_date),
                ('date_maturity', '=', False)]
        elif self.date_type == 'move':
            domain.append(('date', '<=', self.move_date))
        if self.invoice:
            domain.append(('invoice_id', '!=', False))
        if self.payment_mode:
            if self.payment_mode == 'same':
                domain.append(
                    ('payment_mode_id', '=', self.order_id.payment_mode_id.id))
            elif self.payment_mode == 'same_or_null':
                domain += [
                    '|',
                    ('payment_mode_id', '=', False),
                    ('payment_mode_id', '=', self.order_id.payment_mode_id.id)]

        if self.order_id.payment_type == 'outbound':
            # For payables, propose all unreconciled credit lines,
            # including partially reconciled ones.
            # If they are partially reconciled with a supplier refund,
            # the residual will be added to the payment order.
            #
            # For receivables, propose all unreconciled credit lines.
            # (ie customer refunds): they can be refunded with a payment.
            # Do not propose partially reconciled credit lines,
            # as they are deducted from a customer invoice, and
            # will not be refunded with a payment.
            domain += [
                ('credit', '>', 0),
                #  '|',
                ('account_id.internal_type', '=', 'payable'),
                #  '&',
                #  ('account_id.internal_type', '=', 'receivable'),
                #  ('reconcile_partial_id', '=', False),  # TODO uncomment
            ]
        elif self.order_id.payment_type == 'inbound':
            domain += [
                ('debit', '>', 0),
                ('account_id.internal_type', '=', 'receivable'),
                ]
        # Exclude lines that are already in a non-cancelled
        # and non-uploaded payment order; lines that are in a
        # uploaded payment order are proposed if they are not reconciled,
        paylines = self.env['account.payment.line'].search([
            ('state', 'in', ('draft', 'open', 'generated')),
            ('move_line_id', '!=', False)])
        if paylines:
            move_lines_ids = [payline.move_line_id.id for payline in paylines]
            domain += [('id', 'not in', move_lines_ids)]
        return domain

