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

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SolCreateMultiLines(models.TransientModel):

    _inherit = "sale.order.line.create.multi.lines"

    ## change content of 'name' field from Ordernumber to Mapping Remarks
    # (ol.name)
    def _prepare_default_vals_copy(self, ol, ad_iss):
        res = super(SolCreateMultiLines, self)._prepare_default_vals_copy(
                                                                    ol, ad_iss)
        res['name'] = ol.name or False
        return res



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
