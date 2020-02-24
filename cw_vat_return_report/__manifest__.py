# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Codeware LLC
##############################################################################

{
    'name': 'Codeware VAT Return Report',
    'version': '10.0',
    'category': 'Account Vat Report in XLS',
    'description': """
                Account Vat Report in XLS
    """,
    'author': 'Codeware Computing Trading LLC',
    'depends': ['account','report_xlsx','cw_account_vat'],
    'website': 'https://www.odoo.com/page/accounting',
    'data': [
        'wizard/vat_return_report_view.xml',
        'wizard/account_move_line_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
# 'cw_account_vat', 'cw_account_update'