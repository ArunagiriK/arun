# -*- coding: utf-8 -*-

{
    'name': 'Purchase',
    'version': '1.1',
    'category': 'Purchase',
    'summary': 'Manage Purchase Report',
    'description': """
Purchase Report 
===========
""",
    'website': 'http://codewareuae.com',
    'author': 'Arunagiri',
    'depends': ['purchase','base','product'],
    'data': [
        'report/report_purchase_order_template.xml',
        'report/purchase_reports.xml',
    ],
    'demo': [ ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,

}
