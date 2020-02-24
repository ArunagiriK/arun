# -*- coding: utf-8 -*-

{
    'name': 'VAT Detailed Report',
    'version': '11.0',
    'category': 'Account Vat Detailed Report in XLS',
    'description': """
                Account Vat Detailed Report in XLS
    """,
    'depends': ['account', 'account_tax_balance', 'date_range', 'report_xlsx'],
    'data': [
        'views/account_move_line_view.xml',
        'wizard/vat_detailed_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
