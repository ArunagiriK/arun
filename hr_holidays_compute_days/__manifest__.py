# -*- coding: utf-8 -*-


{
    'name': 'Employee Compute Leave Days',
    'version': '12.0.1.0.0',
    'category': 'Human Resources',
    'license': 'AGPL-3',
    'summary': 'Computes the actual leave days '
               'considering rest days and public holidays',
    'author': 'Codeware Arunagiri',
    'website': 'http://codewareuae.com',
    'depends': ['hr', 'hr_contract', 'hr_holidays', 'hr_holidays_public'],
    'data': [
        'views/hr_holidays_status.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
    ],
    'installable': True,
}
