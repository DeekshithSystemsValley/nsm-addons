# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
import base64

class CreditControlRun(models.Model):
    _inherit = "credit.control.run"

    @api.multi
    @api.returns('credit.control.line')
    def _mark_credit_line_as_letter(self, lines):
        lines = lines.filtered(lambda p: not p.partner_id.email)
        lines.write({'channel': 'letter'})
        return lines

    @api.multi
    @api.returns('credit.control.line')
    def _generate_credit_lines(self):
        generated = super(CreditControlRun, self)._generate_credit_lines()
        self._mark_credit_line_as_letter(generated)
        return generated

class CreditCommunication(models.TransientModel):
    _inherit = 'credit.control.communication'

    @api.multi
    @api.returns('mail.message')
    def _generate_chatter_message(self):
        """ Generate message and link to partner chatter"""
        messages = self.env['mail.message']

        report_name = 'account_credit_control.report_credit_control_summary'
        report_obj = self.env['ir.actions.report.xml'].search([('report_name', '=', report_name)], limit=1)

        for comm in self:
            print_name = report_obj.name
            result, format = self.env['report'].get_pdf([comm.id], report_name), 'pdf'

            result = base64.b64encode(result)
            ext = "." + format
            if not print_name.endswith(ext):
                print_name += ext
            attach_fname = print_name
            attach_datas = result

            lines = comm.credit_control_line_ids
            for line in lines:
                body = tools.plaintext2html('Betalingsherinnering/aanmaning verstuurd.')

                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'datas_fname': attach_fname,
                    'res_model': 'mail.compose.message',
                    'type': 'binary',
                }
                attachment = self.env['ir.attachment'].create(data_attach)
                attach = {'attachment_ids':[attachment.id]}
                line.partner_id.message_post(body=body, message_type='notification', **attach)

        return messages

    @api.multi
    @api.returns('credit.control.line')
    def _mark_credit_line_as_sent(self):
        lines = super(CreditCommunication, self)._mark_credit_line_as_sent()
        for comm in self:
            comm._generate_chatter_message()
        return lines
