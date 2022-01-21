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


from openerp.osv import fields, osv, orm


class account_invoice(orm.Model):
    """ Inherits invoice and adds hon boolean to invoice to flag hon-invoices"""
    _inherit = 'account.invoice'


    _columns = {
        'hon': fields.boolean('HON',  help="It indicates that the invoice is a Hon Invoice."),
        'date_publish': fields.date('Publishing Date'),
    }
    _defaults = {
        'hon': False,
    }

    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        invoice = self.pool['account.invoice'].browse(cr, uid, ids, context=context)
        hon = False
        for inv in invoice :
            if inv.hon is True:
                hon = True
        if hon:
            datas = {
                'ids': ids,
                'model': 'account.invoice.hon',
                'form': self.read(cr, uid, ids[0], context=context)
            }
            res = {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.invoice.hon',
                'datas': datas,
                'nodestroy': True
            }
        else:
            datas = {
                'ids': ids,
                'model': 'account.invoice.custom',
                'form': self.read(cr, uid, ids[0], context=context)
            }
            res = {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.invoice.custom',
                'datas': datas,
                'nodestroy': True
            }
        self.write(cr, uid, ids, {'sent': True}, context=context)

        return res

    def action_invoice_sent(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi invoice template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        invoice = self.pool['account.invoice'].browse(cr, uid, ids, context=context)
        hon = False
        for inv in invoice:
            if inv.hon is True:
                hon = True
        if hon:
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'nsm_hon', 'email_template_hon_invoice')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = \
                ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

        else:
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'account', 'email_template_edi_invoice')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

        ctx = dict(context)
        ctx.update({
            'default_model': 'account.invoice',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

class account_invoice_line(orm.Model):
    """ Inherits invoice.line and adds activity from analytic_secondaxis to invoice """
    _inherit = 'account.invoice.line'


    _columns = {
        'activity_id': fields.many2one('project.activity_al', 'Activity'),
        'hon_issue_line_id': fields.many2one('hon.issue.line', 'Hon Issue Line')
    }
