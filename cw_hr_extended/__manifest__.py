# -*- coding: utf-8 -*-
#
#################################################################################
# Author      : Codeware Computer Trading L.L.C. (<www.codewareuae.com>)
# Copyright(c): 2017-Present Codeware Computer Trading L.L.C.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

{
    "name": "Codeware HR Extended",
    'summary': "Codeware HR Extended",
    'description':"Codeware HR Extended",
    'version' : '1.1',
    'category': 'Human Resources',
    'author': 'Codeware Computer Trading L.L.C, {Codeware Team}',
    'website': 'http://www.codewareuae.com',
    "depends": [
        'hr', 
        'hr_contract',
        'hr_attendance',        
        'hr_expense',
        'account_accountant',
        'cw_model_role',
        'cw_update',
    ],
    "demo": [],
    'data':[
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'data/hr_data.xml',
        'data/res.religion.csv',
        'views/template.xml',
        'views/hr_extended_view.xml',

    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
