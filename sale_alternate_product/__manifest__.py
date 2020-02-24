# -*- coding: utf-8 -*-

{
    'name': 'Accounting',
    'version': '1.1',
    'category': 'Sales',
    'summary': 'Manage Sale  and Product',
    'description': """
Accounting Access Rights
========================
It manages the invoice costing for the Accounting 
""",
    'website': 'http://ps-sa.net',
    'author': 'Arunagiri',
    'depends': ['sale','base'],
    'data': [
        'views/sale_views.xml',
        #~ 'security/ir.model.access.csv'
    ],
    'demo': [ ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
