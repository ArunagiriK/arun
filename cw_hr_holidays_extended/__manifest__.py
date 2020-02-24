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
    "name": "Codeware HR Holidays Extended",
    'summary': "Codeware HR Holidays Extended",
    'description':"Codeware HR Holidays Extended",
    'version' : '1.1',
    'category': 'Human Resources',
    'author': 'Codeware Computer Trading L.L.C, {Codeware Team}',
    'company': 'Codeware Computer Trading L.L.C',
    'website': 'http://www.codewareuae.com',
    "depends": [
        'hr_contract',
        'hr_holidays',
        'hr',
        'hr_holidays_compute_days',
        'hr_holidays_expiration',
        'cw_common_clarify',
        'cw_model_role',
        'cw_hr_extended',
        'cw_update',
    ],
    "demo": [],
    'data':[
        #~ 'data/data.xml',
        'data/hr_holidays_status.xml',
        'security/ir.model.access.csv', 
        'security/hr_holidays_security.xml',           
        'views/hr_holidays_view.xml',
        'views/hr_leave_allocation_view.xml',
        'views/hr_holidays_menu_view.xml',  
        #'reports/hr_holidays_template.xml',
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
