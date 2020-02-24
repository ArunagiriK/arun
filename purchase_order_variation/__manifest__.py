# -*- coding: utf-8 -*-
{
    'name': 'Purchase Order Variation',
    'summary': """Purchase Order Variation""",
    'version': '12.0.1.0.0',
    'author': 'Arunagiri',
    'website': "http://coderwareuae.com",
    'company': ' Codeware LLC',
    "category": "Purchase",
    'depends': ['base','purchase','product','product_brand','product_custom'],
    'data': [
             'security/ir.model.access.csv',
             'views/purchase_view.xml',
            ],
    'demo': [
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install':False,
}
