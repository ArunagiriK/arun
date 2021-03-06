# -*- coding: utf-8 -*-
{
    "name" : "Odox Despatch v10",
    "version" : "0.1",
    "author": "Odoxsofthub",
    "category" : "Base",
    "description": """Odoxsofthub Despatch V10""",
    "depends": ['product','sale','account','stock','fleet'],
    "data" : [
             'security/ir.model.access.csv',
             'views/despatch_checklist_seq_view.xml',
             'mail/template.xml',
             'mail/day_report.xml',
             'mail/despatch_report.xml',
            'pricelist/pricelist_view.xml',
            'despatch/despatch_checklist_view.xml',
            'despatch/despatch_view.xml',
            'views/account_view.xml',
            'views/delivery_loc_view.xml',
            'views/od_cartonsize_view.xml',
            'views/transporter_pricelist_view.xml',
            'views/report_template.xml',
           'report/despatch_pdf_report.xml',
            'report/report_despatch_checklist.xml',
            'wizard/despatch_send_wiz_view.xml',
            'wizard/despatch_view.xml',
            'wizard/despatch_datewise_view.xml',
            'wizard/despatch_merge_wizard_view.xml',
            ],
    'css': [],
}
