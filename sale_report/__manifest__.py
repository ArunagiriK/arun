# -*- coding: utf-8 -*-

{
    'name': 'Sales',
    'version': '1.1',
    'category': 'Sale',
    'summary': 'Manage Sale Report Product Existing name',
    'description': """
Sale Report 
===========
Existing Product
""",
    'website': 'http://codewareuae.com',
    'author': 'Arunagiri',
    'depends': ['sale','base','stock'],
    'data': [
        'views/sale_views.xml',
        'report/views/report_sales_template.xml',
        'report/views/report.xml',
        'report/views/report_picking_order.xml',
    ],
    'demo': [ ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,

}
