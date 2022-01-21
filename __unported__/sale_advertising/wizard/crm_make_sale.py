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

from openerp.osv import fields, orm, osv
from openerp.tools.translate import _

from openerp import models, fields as fields2, api, _


class crm_make_sale(orm.TransientModel):
    """ Make sale  order for crm """
    _inherit = "crm.make.sale"

    def _select(self, cr, uid, context=None):
        """
        This function gets default value for partner_id field.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        @return: dict of default values of partner_id fields.
        """
        if context is None:
            context = {}
        lead_obj = self.pool.get('crm.lead')
        active_id = context and context.get('active_id', False) or False
        if not active_id:
            return False
        res = {}
        lead = lead_obj.browse(cr, uid, active_id, context=context)

        if lead:
            res['advertiser'] = lead.published_customer and lead.published_customer.id or False
            res['partner_id'] = lead.partner_id and lead.partner_id.id or False
            res['agent'] = lead.ad_agency_id and lead.ad_agency_id.id or False
        return res

    def _selectPartner(self, cr, uid, context=None):
        res = self._select(cr, uid, context=context)
        return res['partner_id'] if res else False

    def _selectAdvertiser(self, cr, uid, context=None):
        res = self._select(cr, uid, context=context)
        return res['advertiser'] if res else False

    def _selectAgent(self, cr, uid, context=None):
        res = self._select(cr, uid, context=context)
        return res['agent'] if res else False

    def makeOrder(self, cr, uid, ids, context=None):
        """
        This function  create Quotation on given case.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm make sales' ids
        @param context: A standard dictionary for contextual values
        @return: Dictionary value of created sales order.

        Override from sale_crm.crm_make_sale, in which user_id is not
        taken from partner, but just uid.
        """
        if context is None:
            context = {}
        # update context: if come from phonecall, default state values can make the quote crash lp:1017353
        context.pop('default_state', False)

        case_obj = self.pool.get('crm.lead')
        sale_obj = self.pool.get('sale.order')
        partner_obj = self.pool.get('res.partner')
        data = context and context.get('active_ids', []) or []

        for make in self.browse(cr, uid, ids, context=context):
            partner = make.partner_id
            advertiser = make.advertiser
            agent = make.agent
            new_ids = []
            vals = {}
            for case in case_obj.browse(cr, uid, data, context=context):
                if partner and partner.id != case.partner_id.id or advertiser.id != case.published_customer.id or agent.id != case.ad_agency_id.id:
                    partner_addr = partner_obj.address_get(cr, uid, [partner.id],
                                                           ['default', 'invoice', 'delivery', 'contact'])
                    pricelist = partner.property_product_pricelist.id
                    fpos = partner.property_account_position_id and partner.property_account_position_id.id or False
                    payment_term = partner.property_payment_term and partner.property_payment_term.id or False
                    if advertiser:
                        vals['published_customer'] = advertiser and advertiser.id or False,
                    if partner:
                        vals['partner_id'] = partner and partner.id or False
                    if agent:
                        vals['advertising_agency'] = agent and agent.id or False

                    if partner_addr:
                        vals['partner_invoice_id'] = partner_addr['invoice']
                        vals['partner_shipping_id'] = partner_addr['delivery']
                        if partner.type == 'contact':
                            contact = self.pool['res.partner'].search(cr, uid, [('is_company', '=', False),
                                                                                ('type', '=', 'contact'),
                                                                                ('parent_id', '=', partner.id)],
                                                                                context=context)
                            if len(contact) >= 1:
                                contact_id = contact[0]
                            else:
                                contact_id = False
                        elif partner_addr['contact'] == partner_addr['default']:
                            contact_id = False
                        else:
                            contact_id = partner_addr['contact']
                        vals['customer_contact'] = contact_id
                    else:
                        vals['partner_shipping_id'] = partner and partner.id or False
                        vals['partner_invoice_id'] = partner and partner.id or False
                        vals['customer_contact'] = False

                    if False in partner_addr.values():
                        raise osv.except_osv(_('Insufficient Data!'), _('No address(es) defined for this customer.'))
                elif not partner:
                    raise osv.except_osv(_('Insufficient Data!'), _('Something is wrong. No Partner.'))
                else:
                    pricelist = case.partner_id.property_product_pricelist.id
                    fpos = case.partner_id.property_account_position_id and case.partner_id.property_account_position_id.id or False
                    payment_term = case.partner_id.property_payment_term and case.partner_id.property_payment_term.id or False
                    if case.published_customer:
                        vals['published_customer'] = case.published_customer and case.published_customer.id or False
                    if case.partner_id:
                        vals['partner_id'] = case.partner_id and case.partner_id.id or False
                    if case.ad_agency_id:
                        vals['advertising_agency'] = case.ad_agency_id and case.ad_agency_id.id or False
                    if case.partner_invoice_id:
                        vals['partner_invoice_id'] = case.partner_invoice_id and case.partner_invoice_id.id or False
                    if case.partner_shipping_id:
                        vals['partner_shipping_id'] = case.partner_shipping_id and case.partner_shipping_id.id or False
                    else: vals['partner_shipping_id'] = case.partner_id and case.partner_id.id or False
                    if case.partner_contact_id:
                        vals['customer_contact'] = case.partner_contact_id and case.partner_contact_id.id or False
                vals1 = {
                    'origin': _('Opportunity: %s') % str(case.id),
                    'section_id': case.section_id and case.section_id.id or False,
                    'categ_ids': [(6, 0, [categ_id.id for categ_id in case.categ_ids])],
                    # 'shop_id': make.shop_id.id,
                    'pricelist_id': pricelist,
                    'date_order': fields.date.context_today(self, cr, uid, context=context),
                    'fiscal_position': fpos,
                    'payment_term': payment_term,
                    'user_id': uid,
                    'opportunity_subject': case.name,
                }
                vals.update(vals1)
                new_id = sale_obj.create(cr, uid, vals, context=context)
                sale_order = sale_obj.browse(cr, uid, new_id, context=context)
                case_obj.write(cr, uid, [case.id], {'ref': 'sale.order,%s' % new_id})
                new_ids.append(new_id)
                message = _("Opportunity has been <b>converted</b> to the quotation <em>%s</em>.") % (sale_order.name)
                case.message_post(body=message)
            if make.close:
                case_obj.case_close(cr, uid, data)
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
            if len(new_ids) <= 1:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Quotation'),
                    'res_id': new_ids and new_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', new_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'sale.order',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Quotation'),
                    'res_id': new_ids
                }
            return value

    # def _get_shop_id(self, cr, uid, ids, context=None):
    #     cmpny_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
    #     shop = self.pool.get('sale.shop').search(cr, uid, [('company_id', '=', cmpny_id)])
    #     return shop and shop[0] or False

    _columns = {
        # 'shop_id': fields.many2one('sale.shop', 'Shop', required=True),
        'agent': fields.many2one('res.partner', 'Agency', domain=[('customer','=',True),('is_company','=',True),('is_ad_agency','=',True)]),
        'advertiser': fields.many2one('res.partner', 'Advertiser',required=True,
                                      domain=[('customer','=',True),('is_company','=',True),('is_ad_agency','!=',True)]),
        'partner_id': fields.many2one('res.partner', 'Payer', required=True, invisible=True),
        'partner_dummy': fields.related('partner_id', string='Payer', type='many2one', relation='res.partner', readonly=True),
        'close': fields.boolean('Mark Won', help='Check this to close the opportunity after having created the sales order.'),


        # ---
        # Keyword: 'update' causes conflicts hence renamed it to 'update1'
        # --deep
        # 'update': fields.boolean('Update Advertiser/Agency',
        #                         help='Check this to be able to choose (other) advertiser/Agency.'),
        'update1': fields.boolean('Update Advertiser/Agency',
                                help='Check this to be able to choose (other) advertiser/Agency.'),
    }
    _defaults = {
        # 'shop_id': _get_shop_id,
        # 'update': False,
        'update1': False,
        'close': False,
        'advertiser': _selectAdvertiser,
        'partner_id': _selectPartner,
        'partner_dummy': _selectPartner,
        'agent': _selectAgent,
    }


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



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
