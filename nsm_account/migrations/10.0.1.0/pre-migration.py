# -*- coding: utf-8 -*-
# Copyright 2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

to_install = [
    'publishing_accounts',
    'account_invoice_2step_validation'
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
    cr = env.cr
    install_new_modules(env.cr)

    if openupgrade.is_module_installed(env.cr, 'bank_view_improv'):
        openupgrade.update_module_names(
            env.cr,
            [('bank_view_improv', 'nsm_account')],
            merge_modules=True)

    if openupgrade.is_module_installed(env.cr, 'nsm_analytic'):
        openupgrade.update_module_names(
            env.cr,
            [('nsm_analytic', 'nsm_account')],
            merge_modules=True)

    if openupgrade.is_module_installed(env.cr, 'nsm_analytic_2'):
        openupgrade.update_module_names(
            env.cr,
            [('nsm_analytic_2', 'nsm_account')],
            merge_modules=True)

    if openupgrade.is_module_installed(env.cr, 'nsm_invoice_layout'):
        openupgrade.update_module_names(
            env.cr,
            [('nsm_invoice_layout', 'nsm_account')],
            merge_modules=True)

    if openupgrade.is_module_installed(env.cr, 'nsm_merge_to_print_supplier_invoices'):
        openupgrade.update_module_names(
            env.cr,
            [('nsm_merge_to_print_supplier_invoices', 'nsm_account')],
            merge_modules=True)
