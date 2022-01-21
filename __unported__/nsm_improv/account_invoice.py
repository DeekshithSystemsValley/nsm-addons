# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2015 Magnus W.Hulshof
# the GNU Affero General Public License as
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


from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


class account_invoice(osv.osv):
    """ Inherits invoice makes 'invoice.name' visible, 'type' readonly=False  and adds unique SQL constraint for supplier_invoice_number, adds aprofitnummer """
    _inherit = 'account.invoice'
    
    _columns = {
        'name': fields.char('Description', size=64, select=True, readonly=True, states={'draft':[('readonly',False)],'open':[('readonly',False)]}),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', readonly=False, select=True, change_default=True, track_visibility='always'),
        'klantnummer': fields.related('partner_id','aprofit_nummer', type='char', readonly=True, size=64, relation='res.partner', store=False, string='aProfit Klantnummer'),
        # 'internal_number': fields.char('Invoice Number', size=32, readonly=True, states={'draft': [('readonly', False)]}),
    }
    
    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id, journal_id, type)', 'Invoice Number must be unique per Company!'),
        ('supplier_invoice_number_uniq', 'unique(supplier_invoice_number, partner_id)', 'Supplier Invoice Number must be unique for every supplier!'),
    ]
