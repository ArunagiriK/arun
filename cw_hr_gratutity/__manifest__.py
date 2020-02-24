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
    "name": "Codeware HR Employee Gratutity",
    'summary': "Codeware HR Employee Gratutity",
    'description':"Codeware HR Employee Gratutity",
    'version' : '1.1',
    'category': 'Human Resources',
    'author': 'Codeware Computer Trading L.L.C, {Codeware Team}',
    'website': 'http://www.codewareuae.com',
    "depends": [
        'hr', 
        'cw_common_clarify',
        'cw_hr_extended',
        'cw_hr_advance',
        'cw_employee_resign',
        'cw_update',
    ],
    "demo": [],
    'data':[
        
        'data/data.xml',   
        'security/hr_gratutity_security.xml',
        'security/ir.model.access.csv', 
        
        'views/hr_gratutity_view.xml',
        
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
