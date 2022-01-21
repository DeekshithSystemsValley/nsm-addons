# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Magnus Group BV (www.magnus.nl).
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

from openerp.osv import osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import pooler

class account_invoice_portalback(orm.TransientModel):
    """
    This wizard will send  all the selected draft invoices to the supplier Portal
    """

    _name = "account.invoice.portalback"
    _description = "Send the selected invoices to supplier portal"

    def invoice_portalback(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        if context is None:
            context = {}
        pool_obj = pooler.get_pool(cr.dbname)
        data_inv = pool_obj.get('account.invoice').browse(cr, uid, context['active_ids'], context=context)
        m = self.pool['ir.model.data']
        id = m.get_object(cr, uid, 'nsm_hon', 'hon_categoryT').id
        for record in data_inv:
            if record.state != ('draft'):
                raise osv.except_osv(_('Warning!'), _("Selected invoice(s) cannot be sent to portal as they are not in 'Draft' state."))
            if record.product_category.id is id :
                raise osv.except_osv(_('Warning!'), _(
                    "Selected invoice(s) cannot be sent to portal as they have HON Tekst Category."))
            wf_service.trg_validate(uid, 'account.invoice', record['id'], 'portalback', cr)
        return {'type': 'ir.actions.act_window_close'}





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
