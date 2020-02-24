# -*- coding: utf-8 -*-
{
    "name": "Purchase Analysis",
    "category": 'purchase',
    'summary': '',
    "description": """
        
    """,
    "author": "Odox SoftHub",
    "website": "http://odoxsofthub.com/",
    "depends": ['base', 'purchase', 'product','product_brand'],
    "data": [
                'security/ir.model.access.csv',
                'views/purchase_analysis_view.xml',
                'views/res_partner_inherit_view.xml'

    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}