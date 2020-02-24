# -*- coding: utf-8 -*-

{
    'name': 'Inventory',
    'version': '1.1',
    'category': 'Stock',
    'summary': 'Manage Picking Report Qr Code For Product',
    'description': """
Stock Picking Operation Report 

""",
    'website': 'http://ps-sa.net',
    'author': 'Arunagiri',
    'depends': ['stock','base'],
    'data': [
        'views/report/report_stock_picking.xml',
        #~ 'security/ir.model.access.csv'
    ],
    'demo': [ ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
