# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

to_install = [
    'publishing_accounts',
    'account_invoice_2step_validation',
    'nsm_account',

]

def install_new_modules(cr):
    sql = """
    UPDATE ir_module_module
    SET state='to install'
    WHERE name in %s AND state='uninstalled'
    """ % (tuple(to_install),)
    openupgrade.logged_query(cr, sql)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    install_new_modules(env.cr)

    if openupgrade.is_module_installed(env.cr, 'nsm_supportal_extension'):
        openupgrade.update_module_names(
            env.cr,
            [('nsm_supportal_extension', 'nsm_supplier_portal')],
            merge_modules=True)
