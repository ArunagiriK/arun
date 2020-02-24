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
    "name": "Codeware Expiry Notifications",
    'summary': "Codeware Expiry Notifications",
    'description':"Codeware Expiry Notifications",
    'version' : '1.1',
    'category': 'Human Resources',
    'author': 'Codeware Computer Trading L.L.C, {Codeware Team}',
    'website': 'http://www.codewareuae.com',
    "depends": [
        'sale',
        'employee_orientation',
        'hr_holidays',
        'hr_contract',
        'oh_employee_documents_expiry',
        'cw_hr_extended',
        'cw_update',
    ],
    "demo": [],
    'data':[
        'data/template_data.xml',
        'views/template.xml',
        
        'security/hr_expiry_notify_security.xml',
        'security/ir.model.access.csv',       
        
        'views/hr_employee_view.xml',
        'views/hr_expiry_notifications_view.xml',
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
