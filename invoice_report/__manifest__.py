# -*- coding: utf-8 -*-

{
    'name': 'Accounting',
    'version': '1.1',
    'category': 'Accounts',
    'summary': 'Manage Invoice Report',
    'description': """
 Account Invoice  Report 

""",
    'website': 'http://codewaretech.ae',
    'author': 'Arunagiri',
    'depends': ['account','base'],
    'data': [
        'report/views/report_invoice.xml',
        #~ 'security/ir.model.access.csv'
    ],
    'demo': [ ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
