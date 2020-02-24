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
    "name": "Codeware Common Clarify",
    'summary': "Codeware Common Clarify",
    'description':"Codeware Common Clarify",
    'version' : '1.1',
    'category': 'Human Resources',
    'author': 'Codeware Computer Trading L.L.C, {Codeware Team}',
    'website': 'http://www.codewareuae.com',
    "depends": [
        'web',
        'cw_update',
    ],
    "demo": [],
    'data':[       
        
        "security/security.xml",
        "security/ir.model.access.csv",
        
        "views/clarify_view.xml",        
        "wizard/common_clarify_wiz_view.xml",
        "wizard/common_clarify_update_wiz_view.xml",
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
