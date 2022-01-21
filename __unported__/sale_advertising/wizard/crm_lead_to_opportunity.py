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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
import re

class crm_lead2opportunity_partner(osv.osv_memory):
    _inherit = 'crm.lead2opportunity.partner'

    _columns = {
        'action': fields.selection([
            ('exist', 'Link to an existing customer'),
            ('nothing', 'Do not link to a customer')
        ], 'Related Customer', required=True),
        'agent': fields.many2one('res.partner', 'Agency'),
        'advertiser': fields.many2one('res.partner', 'Advertiser'),
        'partner_id': fields.many2one('res.partner', 'Payer'),

        'partner_dummy': fields.related('partner_id', string='Payer', type='many2one', relation='res.partner',
                                        readonly=True),

        # ---
        # Keyword: 'update' causes conflicts hence renamed it to 'update1'
        # --deep
        # 'update': fields.boolean('Update Advertiser/Agency',
        #                          help='Check this to be able to choose (other) Advertiser/Agency.'),
        'update1': fields.boolean('Update Advertiser/Agency',
                                 help='Check this to be able to choose (other) Advertiser/Agency.'),
    }

    _defaults = {
        'action': 'nothing',
        # 'update': False,
        'update1': False,
    }

    def onchange_action(self, cr, uid, ids, action, context=None):
        res = {}
        if action != 'exist':
            res = {
                'partner_id': False,
                'agent': False,
                'advertiser': False,
            }
        else:
            res = self._find_matching_partner(cr, uid, context=context)

        return {'value': res}

    def onchange_advertiser(self, cr, uid, ids, advertiser, update, context):
        if not update:
            # return True
            return {'value': {}}
        data = {'partner_id': advertiser, 'agent': False, 'partner_dummy': advertiser}
        return {'value': data}


    def onchange_agent(self, cr, uid, ids, agent, update, context):
        if not update:
            # return True
            return {'value': {}}
        if agent:
            data = {'partner_id': agent, 'partner_dummy': agent}
            return {'value': data}
        # return True
        return {'value': {}}

    # -- commented by deep
    # def default_get(self, cr, uid, fields, context=None):
    #     """
    #     Default get for name, opportunity_ids.
    #     If there is an exisitng partner link to the lead, find all existing
    #     opportunities links with this partner to merge all information together
    #     """
    #     lead_obj = self.pool.get('crm.lead')
    #     partner_id = self._find_matching_partner(cr, uid, context=context)
    #     #res = super(crm_lead2opportunity_partner, self).default_get(cr, uid, fields, context=context)
    #     res = {}
    #     if context.get('active_id'):
    #         tomerge = set([int(context['active_id'])])
    #
    #         email = False
    #         #partner_id = res.get('partner_id')
    #         lead = lead_obj.browse(cr, uid, int(context['active_id']), context=context)
    #
    #         #TOFIX: use mail.mail_message.to_mail
    #         email = re.findall(r'([^ ,<@]+@[^> ,]+)', lead.email_from or '')
    #
    #         if partner_id:
    #             # Search for opportunities that have the same partner and that arent done or cancelled
    #             ids = lead_obj.search(cr, uid, [('published_customer', '=', partner_id['advertiser']), ('partner_id','=', partner_id['partner_id']),  ('state', '!=', 'done')])
    #             for id in ids:
    #                 tomerge.add(id)
    #         if email:
    #             ids = lead_obj.search(cr, uid, [('email_from', '=ilike', email[0]), ('state', '!=', 'done')])
    #             for id in ids:
    #                 tomerge.add(id)
    #
    #         if 'action' in fields:
    #             res.update({'action' : partner_id['partner_id'] and 'exist'})
    #         if 'partner_id' in fields:
    #             res.update({'partner_id' : partner_id['partner_id']})
    #         if 'advertiser' in fields:
    #             res.update({'advertiser': partner_id['advertiser']})
    #         if 'agent' in fields:
    #             res.update({'agent': partner_id['advertiser']})
    #         if 'name' in fields:
    #             res.update({'name' : len(tomerge) >= 2 and 'merge' or 'convert'})
    #         if 'opportunity_ids' in fields and len(tomerge) >= 2:
    #             res.update({'opportunity_ids': list(tomerge)})
    #
    #     return res

    def default_get(self, cr, uid, fields, context=None):
        """
        Default get for name, opportunity_ids.
        If there is an exisitng partner link to the lead, find all existing
        opportunities links with this partner to merge all information together
        """
        lead_obj = self.pool.get('crm.lead')

        # res = super(crm_lead2opportunity_partner, self).default_get(cr, uid, fields, context=context)
        partner_id = self._find_matching_partner(cr, uid, context=context)

        partnerID = partner_id.get('partner_id', False)
        partner = self.pool.get('res.partner').browse(cr, uid, partnerID)
        res = {}

        if context.get('active_id'):
            tomerge = [int(context['active_id'])]

            # partner_id = res.get('partner_id')
            lead = lead_obj.browse(cr, uid, int(context['active_id']), context=context)
            # email = lead.partner_id and lead.partner_id.email or lead.email_from
            email = partner and partner.email or lead.email_from

            tomerge.extend(self._get_duplicated_leads(cr, uid, partner_id, email, include_lost=True, context=context))
            tomerge = list(set(tomerge))

            if 'action' in fields and not res.get('action'):
                res.update({'action' : partnerID and 'exist' or 'nothing'})
            if 'partner_id' in fields:
                res.update({'partner_id' : partnerID})
            if 'advertiser' in fields:
                res.update({'advertiser': partner_id.get('advertiser', False)})
            if 'agent' in fields:
                res.update({'agent': partner_id.get('advertiser', False)})
            if 'name' in fields:
                res.update({'name' : len(tomerge) >= 2 and 'merge' or 'convert'})
            if 'opportunity_ids' in fields and len(tomerge) >= 2:
                res.update({'opportunity_ids': tomerge})
            if lead.user_id:
                res.update({'user_id': lead.user_id.id})
            if lead.section_id:
                res.update({'section_id': lead.section_id.id})

        return res

    def _find_matching_partner(self, cr, uid, context=None):
        """
        Try to find a matching partner regarding the active model data, like
        the customer's name, email, phone number, etc.

        :return dict partner_id if any, False otherwise
        """
        if context is None:
            context = {}
        partner_id = False
        res = {}
        # The active model has to be a lead or a phonecall
        if (context.get('active_model') == 'crm.lead') and context.get('active_id'):
            active_model = self.pool.get('crm.lead').browse(cr, uid, context.get('active_id'), context=context)
        elif (context.get('active_model') == 'crm.phonecall') and context.get('active_id'):
            active_model = self.pool.get('crm.phonecall').browse(cr, uid, context.get('active_id'), context=context)

        # Find the best matching partner for the active model
        if active_model:
            partner_obj = self.pool.get('res.partner')
            # A partner is set already
            if active_model.partner_id and active_model.published_customer:
                res['advertiser'] = active_model.published_customer.id
                if active_model.partner_id.is_ad_agency:
                    res['agent'] = active_model.ad_agency_id.id
                else:
                    res['agent'] = False
                res['partner_id'] = active_model.partner_id.id
                return res

            # Search through the existing partners based on the lead's email
            elif active_model.email_from:
                partner_ids = partner_obj.search(cr, uid, [('email', '=', active_model.email_from)], context=context)
                if partner_ids:
                    partner_id = partner_ids[0]
            # Search through the existing partners based on the lead's partner or contact name
            elif active_model.partner_name:
                partner_ids = partner_obj.search(cr, uid, [('name', 'ilike', '%'+active_model.partner_name+'%')], context=context)
                if partner_ids:
                    partner_id = partner_ids[0]
            elif active_model.contact_name:
                partner_ids = partner_obj.search(cr, uid, [
                        ('name', 'ilike', '%'+active_model.contact_name+'%')], context=context)
                if partner_ids:
                    partner_id = partner_ids[0]
            partner = partner_obj.browse(cr, uid, partner_id, context=context)
            if partner and partner.is_ad_agency:
                res['agent'] = partner and partner.id or False
                res['partner_id'] = partner and partner.id or False
                res['advertiser'] = False
            elif partner and not partner.is_ad_agency:
                res['advertiser'] = partner and partner.id or False
                res['partner_id'] = partner and partner.id or False
                res['agent'] = False
        return res

    def _convert_opportunity(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        lead = self.pool.get('crm.lead')
        res = False
        partner_ids_map = self._create_partner(cr, uid, ids, context=context)

        lead_ids = vals.get('lead_ids', [])
        team_id = vals.get('section_id', False)
        for lead_id in lead_ids:
            advertiser = partner_ids_map.get(lead_id, False)
            # FIXME: cannot pass user_ids as the salesman allocation only works in batch
            res = lead.convert_opportunity(cr, uid, [lead_id], advertiser, [], team_id, context=context)
        # FIXME: must perform salesman allocation in batch separately here
        user_ids = vals.get('user_ids', False)
        if user_ids:
            lead.allocate_salesman(cr, uid, lead_ids, user_ids, team_id=team_id, context=context)
        return res

    def _create_partner(self, cr, uid, ids, context=None):
        """
        Create partner based on action.
        :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        #TODO this method in only called by crm_lead2opportunity_partner
        #wizard and would probably deserve to be refactored or at least
        #moved to a better place
        if context is None:
            context = {}
        lead = self.pool.get('crm.lead')
        lead_ids = context.get('active_ids', [])
        data = self.browse(cr, uid, ids, context=context)[0]
        advertiser = data.advertiser and data.advertiser.id or False
        return lead.handle_partner_assignation(cr, uid, lead_ids, data.action, advertiser, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
