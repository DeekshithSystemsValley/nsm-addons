# -*- coding: utf-8 -*-
# Copyright 2017 Willem hulshof - <w.hulshof@magnus.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class productCategory(models.Model):
    _inherit = "product.category"


    ad4all = fields.Boolean('Ads to Ad4all', default=False)
    ad4all_material_type = fields.Selection(
        [
            ('PRINT','Print'),
            ('ONLINE','Online'),
            ('DEEL', 'Share'),
        ],
        string='Ad4all Type',
        readonly=False
    )


class productTemplate(models.Model):
    _inherit = "product.template"

    spread = fields.Boolean('Spread: 2/1', default=False)