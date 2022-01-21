# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Magnus www.magnus.nl w.hulshof@magnus.nl
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

#   Adaptation to link Sales Team on Activity for workflow purposes. Register in __ini__.py for deployment

class project_activity_al(osv.osv):
    _inherit = 'project.activity_al'

    _columns = {
            'sales_team_id': fields.many2one('crm.case.section', 'Sales Team' ),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
