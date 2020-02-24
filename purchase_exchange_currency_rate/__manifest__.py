# -*- coding: utf-8 -*-

{
    'name': 'Purchase Currency Rate',
    'version': '12.0.1.0',
    'category': 'Generic Modules/Purchase',
    'sequence': 1,
    'description': """
        App will add invocie currency rate on invocie screen to adjust currency rate 
        
    """,
    'summary':"""odoo app will add Purchase currency rate""",
    'depends': ['base', 'purchase','stock'],
    'data': [
        'views/purchase_view.xml',
        'views/stock_view.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    #author and support Details
    'author': 'CodeWare',
    'website': 'http://www.codewareuae.com',    
    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
