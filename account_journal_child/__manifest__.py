# -*- coding: utf-8 -*-

{
    'name': 'Journal Entry child Company Group',
    'summary': 'Adds the possibility to add a journal entries to a child company',
    'version': '12.0.1.0.0',
    'category': 'Account',
    'author': 'Codeware/Arun',
    'depends': [
        'base',
        'account',
    ],
    'website': 'www.codewareuae.com',
    'data': [   'security/ir.model.access.csv',
                'views/account_move_views.xml',
                'views/account_move_template_views.xml'

],
    'installable': True,
    'auto_install':False,
}
