# -*- coding: utf-8 -*-

{
    'name': 'Sales stock Picking',
    'version': '1.1',
    'category': 'Sales Stock',
    'summary': 'Manage Sale And Picking',
    'description': """
Sale Stock 

""",
    'website': 'http://codewaretech.ae',
    'author': 'Arunagiri',
    'depends': ['sale','stock_account','base','product_substitution'],
    'data': [
        'views/sale_views.xml',
        'views/stock_picking_views.xml',
        
    ],
    'demo': [ ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,

}
