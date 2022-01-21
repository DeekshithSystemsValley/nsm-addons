# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Eurogroup Consulting BV (www.eurogroupconsulting.nl).
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

from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler

class account_invoice_author(osv.osv_memory):
    """
    This wizard will authorize  all the selected open invoices for payment
    """

    _name = "account.invoice.author"
    _description = "Authorize the selected invoices"

    def invoice_author(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        if context is None:
            context = {}
        pool_obj = pooler.get_pool(cr.dbname)
        data_inv = pool_obj.get('account.invoice').read(cr, uid, context['active_ids'], ['state'], context=context)

        for record in data_inv:
            if record['state'] != ('open'):
                raise osv.except_osv(_('Warning!'), _("Selected invoice(s) cannot be authorized as they are not in 'Open' state."))
            wf_service.trg_validate(uid, 'account.invoice', record['id'], 'invoice_auth', cr)
        return {'type': 'ir.actions.act_window_close'}

account_invoice_author()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
