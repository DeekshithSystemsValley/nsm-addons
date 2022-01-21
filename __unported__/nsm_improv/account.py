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


import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv, expression
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools.safe_eval import safe_eval as eval

import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class account_move(osv.osv):
    _name = "account.move"
    _inherit = ['account.move', 'mail.thread']
    _track = {
        'state': {
         'nsm_improv.mt_move_unposted': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'draft',
         'nsm_improv.mt_move_posted': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'posted',
         }
    }
    _columns = {
        'state': fields.selection([('draft', 'Unposted'), ('posted', 'Posted')], 'Status', required=True, readonly=True,
                                  track_visibility='onchange',
                                  help='All manually created new journal entries are usually in the status \'Unposted\', but you can set the option to skip that status on the related journal. In that case, they will behave as journal entries automatically created by the system on document validation (invoices, bank statements...) and will be created in \'Posted\' status.'),
        # 'period_id': fields.many2one('account.period', 'Period', required=True, states={'posted': [('readonly', True)]},
        #                              track_visibility='onchange'),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True,
                                      states={'posted': [('readonly', True)]}, track_visibility='onchange'),
    }

    # --deep: Below method is not needed: it has been revised in Odoo 9
    # def post(self, cr, uid, ids, context=None):
    #     if context is None:
    #         context = {}
    #     invoice = context.get('invoice', False)
    #     valid_moves = self.validate(cr, uid, ids, context)
    #
    #     if not valid_moves:
    #         raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
    #     obj_sequence = self.pool.get('ir.sequence')
    #     for move in self.browse(cr, uid, valid_moves, context=context):
    #         if move.name =='/':
    #             new_name = False
    #             journal = move.journal_id
    #
    #             if invoice and invoice.internal_number:
    #                 new_name = invoice.internal_number
    #             else:
    #                 if journal.sequence_id:
    #                     c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
    #                     new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
    #                 else:
    #                     raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))
    #
    #             if new_name:
    #                 self.write(cr, uid, [move.id], {'name':new_name})
    #
    #     #cr.execute('UPDATE account_move '\
    #     #           'SET state=%s '\
    #     #           'WHERE id IN %s',
    #     #           ('posted', tuple(valid_moves),))
    #     result = super(account_move, self).write(cr, uid, valid_moves, {'state':'posted'})
    #     return result

    def button_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if not line.journal_id.update_posted:
                raise osv.except_osv(_('Error!'), _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
        if ids:
         #   cr.execute('UPDATE account_move '\
         #              'SET state=%s '\
         #              'WHERE id IN %s', ('draft', tuple(ids),))
            self.write(cr, uid, ids, {'state':'draft'})
        return True


account_move()
