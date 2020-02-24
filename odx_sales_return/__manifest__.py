{
    'name': 'Sales Direct Return',
    'version': '12.0',
    'author': "odoxsofthub",
    'depends': ['sale_stock','sale_management','base','stock'],
    'demo': [],
    'description': """
            Sales Return in Sales forms
    """,
    'data': ['security/ir.model.access.csv',
             'views/sales_return_view.xml',
             'views/ir_sequence_data.xml',
        ],
    'test': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: