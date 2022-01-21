# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2016 Magnus (<http://www.magnus.nl>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp
import time
from openerp.tools.translate import _
from openerp.tools import email_re, email_split


class crm_lead(orm.Model):
    _inherit = "crm.lead"
    _columns = {
        'published_customer': fields.many2one('res.partner', 'Advertiser', domain=[('customer', '=', True)], ondelete='set null',
                                              track_visibility='onchange',
                                        select=True,
                                        help="Linked Advertiser (optional). "),
        'partner_id': fields.many2one('res.partner', 'Payer', ondelete='set null', track_visibility='onchange',
                                        select=True,
                                        help="Linked Payer (optional)."),
        'partner_invoice_id': fields.many2one('res.partner', 'Payer Invoice Address', ondelete='set null',
                                      select=True,
                                      help="Linked partner (optional). Usually created when converting the lead."),
        'partner_shipping_id': fields.many2one('res.partner', 'Payer Delivery Address', ondelete='set null',
                                              select=True,
                                              help="Linked partner (optional). Usually created when converting the lead."),
        'partner_contact_id': fields.many2one('res.partner', 'Contact Person', ondelete='set null', track_visibility='onchange',
                                        select=True,
                                        help="Linked Contact Person (optional). Usually created when converting the lead."),
        'ad_agency_id': fields.many2one('res.partner', 'Agency', ondelete='set null', track_visibility='onchange',
                                      select=True,
                                      help="Linked Advertising Agency (optional). Usually created when converting the lead."),
        'partner_acc_mgr': fields.related('partner_id', 'user_id', type='many2one', relation='res.users',
                                          string='Account Manager', store=True),

    }

    def onchange_published_customer(self, cr, uid, ids, published_customer, context):
        values = {}
        if published_customer:
            advertiser = self.pool.get('res.partner').browse(cr, uid, published_customer, context=context)
            values = {
                'partner_name': advertiser.name,
                'partner_id': published_customer,
                'title': advertiser.title and advertiser.title.id or False,
                'email_from': advertiser.email,
                'phone': advertiser.phone,
                'mobile': advertiser.mobile,
                'fax': advertiser.fax,
                'zip': advertiser.zip,
                'function': advertiser.function,
                'ad_agency_id': False,
            }
        return {'value' : values }

    def onchange_agency(self, cr, uid, ids, ad_agency, context):
        values = {}
        if ad_agency:
            agency = self.pool.get('res.partner').browse(cr, uid, ad_agency, context=context)
            values = {
                'partner_id': ad_agency,
                'title': agency.title and agency.title.id or False,
                'email_from': agency.email,
                'phone': agency.phone,
                'mobile': agency.mobile,
                'fax': agency.fax,
                'zip': agency.zip,
                'function': agency.function,
            }
        return {'value' : values}

    def onchange_partner(self, cr, uid, ids, part, context=None):
        if not part:
            return {}

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['delivery', 'invoice', 'contact'])
        values = {}

        if part.type == 'contact':
            contact = self.pool['res.partner'].search(cr, uid, [('is_company','=', False),('type','=', 'contact'),('parent_id','=', part.id)], context=context)
            if len(contact) >=1:
                contact_id = contact[0]
            else:
                contact_id = False
        elif addr['contact'] == addr['default']:
            contact_id = False
        else: contact_id = addr['contact']
        invoice = self.pool.get('res.partner').browse(cr, uid, addr['invoice'], context=context)

        values = {
            'street': invoice.street,
            'street2': invoice.street2,
            'city': invoice.city,
            'state_id': invoice.state_id and invoice.state_id.id or False,
            'country_id': invoice.country_id and invoice.country_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'partner_contact_id': contact_id,
        }
        return {'value' : values}


    def onchange_contact(self, cr, uid, ids, partner_id, context=None):
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            values = {
                'contact_name': partner.name,
                'title': partner.title and partner.title.id or False,
                'email_from' : partner.email,
                'phone' : partner.phone,
                'mobile' : partner.mobile,
                'fax' : partner.fax,
                'function': partner.function,
            }
        else:
            values['contact_name'] = False
        return {'value' : values}

    def _convert_opportunity_data(self, cr, uid, lead, advertiser, section_id=False, context=None):
        crm_stage = self.pool.get('crm.case.stage')

        if not section_id:
            section_id = lead.section_id and lead.section_id.id or False

        val = {
            'planned_revenue': lead.planned_revenue,
            'probability': lead.probability,
            'name': lead.name,
            'partner_name': lead.partner_name,
            'contact_name': lead.contact_name,
            'street': lead.street,
            'street2': lead.street2,
            'zip': lead.zip,
            'city': lead.city,
            'state_id': lead.state_id and lead.state_id.id or False,
            'country_id': lead.country_id and lead.country_id.id or False,
            'title': lead.title and lead.title.id or False,
            'email_from': lead.email_from,
            'function': lead.function,
            'phone': lead.phone,
            'mobile': lead.mobile,
            'fax': lead.fax,
            'categ_ids': [(6, 0, [categ_id.id for categ_id in lead.categ_ids])],
            'user_id': (lead.user_id and lead.user_id.id),
            'type': 'opportunity',
            'date_action': fields.datetime.now(),
            'date_open': fields.datetime.now(),
        }
        if advertiser:
            val['published_customer'] = advertiser and advertiser.id or False,
        if lead.partner_id:
            val['partner_id'] = lead.partner_id and lead.partner_id.id or False,
        if lead.ad_agency_id:
            val['ad_agency_id'] = lead.ad_agency_id and lead.ad_agency_id.id or False,
        if lead.partner_invoice_id:
            val['partner_invoice_id'] = lead.partner_invoice_id and lead.partner_invoice_id.id or False,
        if lead.partner_shipping_id:
            val['partner_shipping_id'] = lead.partner_shipping_id and lead.partner_shipping_id.id or False,
        if lead.partner_contact_id:
            val['partner_contact_id'] = lead.partner_contact_id and lead.partner_contact_id.id or False,

        if not lead.stage_id or lead.stage_id.type=='lead':
            val['stage_id'] = self.stage_find(cr, uid, [lead], section_id, [('state', '=', 'draft'),('type', 'in', ('opportunity','both'))], context=context)
        return val

    def convert_opportunity(self, cr, uid, ids, advertiser, user_ids=False, section_id=False, context=None):
        payer = False
        if advertiser:
            partner = self.pool.get('res.partner')
            adv = partner.browse(cr, uid, advertiser, context=context)

        for lead in self.browse(cr, uid, ids, context=context):
            # if lead.state in ('done', 'cancel'):
            #     continue
            vals = self._convert_opportunity_data(cr, uid, lead, adv, section_id, context=context)
            self.write(cr, uid, [lead.id], vals, context=context)
        self.message_post(cr, uid, ids, body=_("Lead <b>converted into an Opportunity</b>"), subtype="crm.mt_lead_convert_to_opportunity", context=context)

        if user_ids or section_id:
            self.allocate_salesman(cr, uid, ids, user_ids, section_id, context=context)

        return True

    def handle_partner_assignation(self, cr, uid, ids, action='create', advertiser=False, context=None):
        """
        Handle partner assignation during a lead conversion.
        if action is 'create', create new partner with contact and assign lead to new partner_id.
        otherwise assign lead to the specified partner_id

        :param list ids: leads/opportunities ids to process
        :param string action: what has to be done regarding partners (create it, assign an existing one, or nothing)
        :param int partner_id: partner to assign if any
        :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        #TODO this is a duplication of the handle_partner_assignation method of crm_phonecall
        advertiser_ids = {}
        # If a partner_id is given, force this partner for all elements
        force_advertiser_id = advertiser
        for lead in self.browse(cr, uid, ids, context=context):
            # If the action is set to 'create' and no partner_id is set, create a new one
            # if action == 'create':
            if action in ('create', 'nothing'):
                advertiser = force_advertiser_id or self._create_lead_partner(cr, uid, lead, context)
            self._lead_set_partner(cr, uid, lead, advertiser, context=context)
            advertiser_ids[lead.id] = advertiser
        return advertiser_ids

    def allocate_salesman(self, cr, uid, ids, user_ids=None, team_id=False, context=None):
        """
        Assign salesmen and salesteam to a batch of leads.  If there are more
        leads than salesmen, these salesmen will be assigned in round-robin.
        E.g.: 4 salesmen (S1, S2, S3, S4) for 6 leads (L1, L2, ... L6).  They
        will be assigned as followed: L1 - S1, L2 - S2, L3 - S3, L4 - S4,
        L5 - S1, L6 - S2.

        :param list ids: leads/opportunities ids to process
        :param list user_ids: salesmen to assign
        :param int team_id: salesteam to assign
        :return bool
        """
        index = 0

        for lead_id in ids:
            value = {}
            if team_id:
                value['section_id'] = team_id
            if user_ids:
                value['user_id'] = user_ids[index]
                # Cycle through user_ids
                index = (index + 1) % len(user_ids)
            if value:
                self.write(cr, uid, [lead_id], value, context=context)
        return True

    def _lead_set_partner(self, cr, uid, lead, advertiser, context=None):
        """
        Assign a advertiser to a lead.

        :param object lead: browse record of the lead to process
        :param int advertiser: identifier of the advertiser to assign
        :return bool: True if the advertiser has properly been assigned
        """
        res = False
        res_partner = self.pool.get('res.partner')
        if advertiser:
            res_partner.write(cr, uid, advertiser, {'section_id': lead.section_id and lead.section_id.id or False})
            contact_id = res_partner.address_get(cr, uid, [advertiser])['default']
            # res = lead.write({'published_customer': advertiser}, context=context)
            # TODO: FIXME, check is this correct?
            res = lead.write({'published_customer': advertiser, 'partner_id': advertiser}, context=context)
            message = _("<b>Advertiser</b> set to <em>%s</em>." % (lead.published_customer.name))
            self.message_post(cr, uid, [lead.id], body=message, context=context)
        return res



    # -- deep added
    def _get_duplicated_leads_by_emails(self, cr, uid, partner_id, email, include_lost=False, context=None):
        """
        Search for opportunities that have   the same partner and that arent done or cancelled
        """

        final_stage_domain = [('stage_id.probability', '<', 100), '|', ('stage_id.probability', '>', 0), ('stage_id.sequence', '<=', 1)]
        partner_match_domain = []
        for email in set(email_split(email) + [email]):
            partner_match_domain.append(('email_from', '=ilike', email))
        if partner_id:
            partner_match_domain.append(('partner_id', '=', partner_id['partner_id']))
            partner_match_domain.append(('published_customer', '=', partner_id['advertiser']))
        partner_match_domain = ['|'] * (len(partner_match_domain) - 1) + partner_match_domain
        if not partner_match_domain:
            return []
        domain = partner_match_domain
        if not include_lost:
            domain += final_stage_domain

        return self.search(cr, uid, domain, context=context)




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

