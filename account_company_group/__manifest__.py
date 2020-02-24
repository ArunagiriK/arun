# -*- coding: utf-8 -*-

{
    'name': 'Chart Of account Company Group',
    'summary': 'Adds the possibility to add a company group to a company',
    'version': '12.0.1.0.0',
    'category': 'Account',
    'author': 'Codeware/Arun',
    'depends': [
        'base',
        'account',
    ],
    'website': 'www.codewareuae.com',
    'data': ['wizard/account_wizard.xml',
              'views/res_config_settings_views.xml',
              'views/inherited_account_view.xml'
],
    'installable': True,
    'auto_install':False,
}
