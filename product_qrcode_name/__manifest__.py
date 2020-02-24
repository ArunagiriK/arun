# -*- coding: utf-8 -*-

{
    'name': 'Product QR  Sequence Name',
    'version': '1.0',
    'category': 'All',
    'author': 'codeware-Arunagiri',
    'summary': 'Product QR Code Sequence ',
    'description': """


Product QR Code Sequence 

""",
    'depends': ['product'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_views.xml',
        # 'views/templates.xml'
    ],
    'qweb': [
        # 'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/label.jpg',
    ],
    'installable': True,
    'website': 'codewareuae.com',
}
