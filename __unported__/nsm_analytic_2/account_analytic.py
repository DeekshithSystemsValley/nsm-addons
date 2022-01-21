# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Magnus.nl
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
from openerp.osv import fields
from openerp.tools.translate import _

class account_analytic(osv.osv):
    _inherit = 'account.analytic.account'
    

    _columns = {
        'code': fields.char('Reference', select=True, required=True, track_visibility='onchange'),
        # 'section_ids': fields.many2many('crm.case.section','analytic_section_rel','analytic_account_id','section_id','Sales Teams'),
        'section_ids': fields.many2many('crm.team','analytic_section_rel','analytic_account_id','section_id','Sales Teams'),
        'department_id': fields.many2one('hr.department', 'Department'),
    }
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code Analytic Account must be unique!'),
    ]

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}
        if name:
            account_ids = self.search(cr, uid, [('code', '=ilike', name + "%")] + args, limit=limit, context=context)
            if not account_ids:
                dom = []
                for name2 in name.split('/'):
                    name = name2.strip()
                    account_ids = self.search(cr, uid, dom + [('name', operator, name)] + args, limit=limit, context=context)
                    if not account_ids: break
                    dom = [('parent_id','in',account_ids)]
        else:
            account_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, account_ids, context=context)

account_analytic()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
