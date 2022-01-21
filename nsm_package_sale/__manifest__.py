# -*- coding: utf-8 -*-
{
    'name': "nsm_package_sale",

    'summary': """
        Package Sale""",

    'description': """
        
    """,

    'author': 'Magnus - Willem Hulshof',
    'website': 'http://www.magnus.nl',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale','package_sale_advertising_order'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # "report/report_saleorder.xml",
        'views/sale_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}