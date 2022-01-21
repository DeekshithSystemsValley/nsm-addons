# -*- coding: utf-8 -*-


from openupgradelib import openupgrade




def map_paymentOrder_state(cr):
    # Mapping values of state field for account_payment_order.
    openupgrade.map_values(
        cr,
        openupgrade.get_legacy_name('state'), 'state',
        [('open', 'open'), ('sent', 'generated')],
        table='account_payment_order', write='sql')


@openupgrade.migrate()
def migrate(cr, version):
    map_paymentOrder_state(cr)
