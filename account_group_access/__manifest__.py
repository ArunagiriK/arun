# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Account Validate Access',
    'version': '2.0',
    'category': 'Human Resources',
    'summary': 'Manage Account Access',
    'description': """
This module aims to manage Account's Access
       """,
    'website': 'http://codewareuae.com',
    'depends': ['base','account','sale','purchase'],
    'author':'Arunagiri',
    'data': [
        'security/account_group_security.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_views.xml'
        #~ 'security/ir.model.access.csv',
        
    ],
    'demo': [
        
    ],
    'installable': True,
    'auto_install': False,
    'qweb': [
       
    ],
    'application': True,
}
