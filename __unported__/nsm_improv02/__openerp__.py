# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Magnus - Willem Hulshof - www.magnus.nl
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company like Veritos.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

{
    'name': 'nsm_improv02',
    'version': '1.0',
    'category': 'workflow',
    'description': """
This module adds a verification step in the invoice authorization flow in Odoo.
=====================================================================================


    """,
    'author': 'Magnus - Willem Hulshof',
    'website': 'http://www.magnus.nl',
    'depends': ['account', 'nsm_expense', 'megis_auth',
                ],
    'data': ["account_security.xml",
             "account_view.xml",
             "account_invoice_view.xml",
             "account_invoice_state_view.xml",
             "account_invoice_workflow.xml",
             "res_company_view.xml",
             "ir.model.access.csv",
             ],
    'demo': [],
    'installable': False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
