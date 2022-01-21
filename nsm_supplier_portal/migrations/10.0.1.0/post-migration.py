# -*- coding: utf-8 -*-
from openupgradelib import openupgrade

# from openerp.modules.registry import RegistryManager
from odoo import SUPERUSER_ID

#
# _xmlid_renames = [
#     ('megis_auth.goedk_facturen', 'account_invoice_2step_validation.goedk_facturen'),
#     ('megis_auth.authorize', 'account_invoice_2step_validation.authorize'),
#     ('megis_auth.verification', 'account_invoice_2step_validation.verification'),
# ]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr

    env['ir.module.module'].sudo(SUPERUSER_ID).update_list()

    # openupgrade.rename_xmlids(env.cr, _xmlid_renames)

    # # Install alternate modules:
    # cr.execute("""
    #     UPDATE ir_module_module set state = 'to install'
    #     WHERE name in ('sale_advertising_order', 'publishing_accounts', 'fetchmail_company_invoice',
    #                    'freelancer_self_billing', 'nsm_account', 'account_invoice_2step_validation');
    # """)
    #
    # #---------------------------------------------------------------
    # # Removing deprecated / Clubbed modules
    # cr.execute("""
    #     UPDATE ir_module_module set state = 'to remove'
    #     WHERE name in ('nsm_invoice_layout', 'web_m2x_options', 'nsm_merge_to_print_supplier_invoices',
    #                    'nsm_analytic', 'nsm_supportal_extension', 'nsm_analytic_2', 'nsm_improv02',
    #                    'sale_advertising', 'nsm_improv', 'nsm_hon', 'megis_auth', 'fetchmail_company_setting',
    #                    'fetchmail_invoice', 'bank_view_improv');
    # """)
    #
