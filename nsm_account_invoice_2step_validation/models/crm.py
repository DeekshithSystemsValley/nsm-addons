# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CrmTeam(models.Model):
    _inherit = "crm.team"

    member_ids = fields.Many2many('res.users', 'crm_team_user_rel','sale_team_id', 'user_id', string='Team Members')
