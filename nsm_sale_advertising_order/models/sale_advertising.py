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

from odoo import api, fields, models, _
import json

class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    material_contact_person = fields.Many2one('res.partner', 'Material Contact Person', domain=[('customer','=',True)])

    @api.multi
    def action_approve1(self):
        res = super(SaleOrder, self).action_approve1()
        orders = self.filtered(lambda s: s.state in ['approved1'])
        for order in orders:
            olines = []
            for line in order.order_line:
                if line.multi_line:
                    olines.append(line.id)
            if olines:
                list = self.env['sale.order.line.create.multi.lines'].create_multi_from_order_lines(orderlines=olines)
                newlines = self.env['sale.order.line'].browse(list)
                for newline in newlines:
                    if newline.deadline_check():
                        newline.page_qty_check_create()
        return res

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    @api.depends('adv_issue', 'product_template_id')
    def name_get(self):
        result = []
        for sol in self:
            name = sol.adv_issue.name if sol.adv_issue else ""
            if sol.product_template_id:
                name = name+' ('+sol.product_template_id.name+')'
                result.append((sol.id, name))
        return result

    @api.depends('state')
    def _get_indeellijst_data(self):
        for line in self:
            prod = line.product_id
            if prod:
                line.product_width = prod.width
                line.product_height = prod.height
                line.material_id = line.recurring_id.id if line.recurring_id else line.id


    @api.depends('proof_number_payer','proof_number_adv_customer')
    def _get_proof_data(self):
        for line in self:
            proof_payer = line.proof_number_payer
            proof_cus = line.proof_number_adv_customer and line.proof_number_adv_customer[0]
            if proof_payer:
                line.proof_parent_name = proof_payer.parent_id and proof_payer.parent_id.name or False
                line.proof_initials = proof_payer.initials or ''
                line.proof_infix = proof_payer.infix or ''
                line.proof_lastname = proof_payer.lastname or ''
                line.proof_country_code = proof_payer.country_id.code or ''
                line.proof_zip = proof_payer.zip or ''
                line.proof_street_number = proof_payer.street_number or ''
                line.proof_street_name = proof_payer.street_name or ''
                line.proof_city = proof_payer.city or ''
                line.proof_partner_name = proof_payer.name or ''
            elif proof_cus:
                line.proof_parent_name = proof_cus.parent_id and proof_cus.parent_id.name or False
                line.proof_initials = proof_cus.initials or ''
                line.proof_infix = proof_cus.infix or ''
                line.proof_lastname = proof_cus.lastname or ''
                line.proof_country_code = proof_cus.country_id.code or ''
                line.proof_zip = proof_cus.zip or ''
                line.proof_street_number = proof_cus.street_number or ''
                line.proof_street_name = proof_cus.street_name or ''
                line.proof_city = proof_cus.city or ''
                line.proof_partner_name = proof_cus.name or ''

    @api.model
    def default_get(self, fields_list):
        result = super(SaleOrderLine, self).default_get(fields_list)
        if 'customer_contact' in self.env.context:
            result.update({'proof_number_payer':self.env.context['customer_contact']})
            result.update({'proof_number_amt_payer': 1})

        result.update({'proof_number_adv_customer': False})
        result.update({'proof_number_amt_adv_customer': 0})
        return result


    @api.onchange('ad_class')
    def onchange_ad_class(self):
        res = super(SaleOrderLine, self).onchange_ad_class()
        if not self.advertising:
            return res
        if self.ad_class:
            res['value']['is_plusproposition_category'] = self.ad_class.is_plusproposition_category
        return res

    @api.onchange('circulation_type')
    def onchange_circulation_type(self):
        self.selective_circulation = self.circulation_type.selective_circulation if self.circulation_type else False

    @api.onchange('proof_number_adv_customer')
    def onchange_proof_number_adv_customer(self):
        self.proof_number_amt_adv_customer = 1 if self.proof_number_adv_customer else 0

    @api.onchange('proof_number_amt_adv_customer')
    def onchange_proof_number_amt_adv_customer(self):
        if self.proof_number_amt_adv_customer <= 0: self.proof_number_adv_customer = False

    @api.onchange('proof_number_amt_payer')
    def onchange_proof_number_amt_payer(self):
        if self.proof_number_amt_payer < 1: self.proof_number_payer = False

    @api.onchange('proof_number_payer')
    def onchange_proof_number_payer(self):
        self.proof_number_amt_payer = 1 if self.proof_number_payer else 0

    @api.depends('ad_class','title','title_ids')
    @api.multi
    def _compute_product_template_domain(self):
        """
        Compute domain for the field product_template_id.
        """
        for rec in self:
            titles = rec.title_ids if rec.title_ids else rec.title or False
            domain = []
            if titles:
                product_ids = rec.env['product.product']
                for title in titles:
                    if title.product_attribute_value_id:
                        ids = product_ids.search([('attribute_value_ids', '=', [title.product_attribute_value_id.id])])
                        product_ids += ids
                product_tmpl_ids = product_ids.mapped('product_tmpl_id').ids
                domain += [('id', 'in', product_tmpl_ids)]
            if rec.ad_class:
                domain += [('categ_id', '=', rec.ad_class.id)]
            rec.product_template_domain = json.dumps(domain)

    proof_number_payer = fields.Many2one('res.partner', 'Proof Number Payer')
    proof_number_adv_customer = fields.Many2many('res.partner', 'partner_line_proof_rel', 'line_id', 'partner_id', string='Proof Number Advertising Customer')
    proof_number_amt_payer = fields.Integer('Proof Number Amount Payer', default=1)
    proof_number_amt_adv_customer = fields.Integer('Proof Number Amount Advertising', default=1)
    proof_parent_name = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Parent")
    proof_initials = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Initials")
    proof_infix = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Infix")
    proof_lastname = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Last Name")
    proof_country_code = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Country Code")
    proof_zip = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Zip")
    proof_street_number = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Street Number")
    proof_street_name = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Street Name")
    proof_city = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="City")
    proof_partner_name = fields.Char(compute='_get_proof_data', readonly=True, store=False, string="Name")
    product_width = fields.Float(compute='_get_indeellijst_data', readonly=True, store=False, string="Width")
    product_height = fields.Float(compute='_get_indeellijst_data', readonly=True, store=False, string="Height")
    material_id = fields.Integer(compute='_get_indeellijst_data', readonly=True, store=False, string="Material ID")
    plus_proposition_weight = fields.Integer(string='Plusproposition Weight')
    plus_proposition_height = fields.Integer(string='Plusproposition Height')
    plus_proposition_width = fields.Integer(string='Plusproposition Width')
    is_plusproposition_category = fields.Boolean(string='Plusproposition')
    selective_circulation = fields.Boolean(string='Selective Circulation')
    circulation_description = fields.Text(string='Circulation Description')
    circulation_type = fields.Many2one('circulation.type', string='Circulation Type')
    send_with_advertising_issue = fields.Boolean(string="Send with advertising issue")
    adv_issue_parent = fields.Many2one(related='adv_issue.parent_id', string='Advertising Issue Parent', readonly=True, store=True)
    product_template_domain = fields.Char(compute="_compute_product_template_domain", string="Product Template Domain")



