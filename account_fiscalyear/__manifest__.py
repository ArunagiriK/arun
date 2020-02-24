# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Account FiscalYear and Periods',
    'version': '1.0',
    'category': 'Account',
    'summary': 'Account FiscalYear and Periods',
    'description': """
Account FiscalYear and Periods
==============================
This application create Account Fiscal Years and Periods.
        """,
    'author': 'Codeware.',
    'website': 'https://www.codewareuae.com/',
    'depends': [
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_fiscalyear_view.xml',
        'wizard/account_fiscalyear_close_view.xml',
        'wizard/account_fiscalyear_period_close_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
