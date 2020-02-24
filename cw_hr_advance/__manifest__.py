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
    "name": "Codeware HR Advance",
    'summary': "Codeware HR Advance",
    'description':"Codeware HR Advance",
    'version' : '1.1',
    'category': 'Human Resources',
    'author': 'Codeware Computer Trading L.L.C, {Codeware Team}',
    'website': 'http://www.codewareuae.com',
    "depends": [
        'hr', 
        'hr_payroll',
        'cw_common_clarify',
        'cw_hr_extended',
        'cw_update',
    ],
    "demo": [],
    'data':[             
        'data/hr_advance_request_data.xml',   
        'security/ir.model.access.csv',
        'security/hr_advance_request_security.xml',
        'views/hr_advance_request_view.xml',        
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: