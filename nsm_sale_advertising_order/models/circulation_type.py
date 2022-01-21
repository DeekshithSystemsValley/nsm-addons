# -*- coding: utf-8 -*-
# Copyright 2017 Willem hulshof - <w.hulshof@magnus.nl>

from odoo import api, fields, models, _

class CirculationType(models.Model):
    _name = "circulation.type"
    _description = "Circulation Type"

    name = fields.Char(string='Circulation Type', translate=True)
    selective_circulation = fields.Boolean(string='Selective Circulation')