# -*- coding: utf-8 -*-

{
    'name': 'Product QR Code',
    'version': '1.0',
    'category': 'All',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Product QR Code allows you to add QR code information and print QR code in product labels also.',
    'description': """

=======================
Product QR Code allows you to add QR code information and print QR code in product labels also.

""",
    'depends': ['product'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml'
    ],
    'qweb': [
        # 'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/label.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 10,
    'currency': 'EUR',
}
