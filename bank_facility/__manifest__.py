# -*- coding: utf-8 -*-
{
    'name': 'Bank Facility',
    'summary': """Bank Facility""",
    'version': '12.0.1.0.0',
    'author': 'Arunagiri',
    'website': "http://ps-sa.net",
    'company': ' Pioneer Solutions',
    "category": "Manufaturing",
    'depends': ['base','account','payment'],
    'data': [
             'security/ir.model.access.csv',
             'wizard/repayment_view.xml',
             'views/bank_facility_views.xml',
             'views/account_payment.xml',
             'views/res_company.xml',
             'menu/menu.xml'
              
],
    'demo': [
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install':False,
}
