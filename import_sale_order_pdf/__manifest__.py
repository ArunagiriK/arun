# -*- coding: utf-8 -*-
{
    'name': 'Import Sale Order',
    'summary': """Import sale order pdf""",
    'version': '12.0.1.0.0',
    'author': 'Arunagiri',
    'website': "http://codeware.ae",
    'company': 'Codeware',
    "category": "Sale",
    'depends': ['base','sale'],
    'data': [
             'wizard/import_sale_view.xml',
             'views/sale_views.xml',
             'views/product_view.xml'
              
],
    'demo': [
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install':False,
}
