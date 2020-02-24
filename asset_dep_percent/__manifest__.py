{
    'name': 'Asset Depreciation Based on Percentage',
    'version': '1.0',
    'author': 'Codeware/Niyas',
    'website': 'www.codewareuae.com',
    'depends': ['account_asset'],
    'demo': [],
    'description': """
Add Percentage as depreciation method
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/asset_view.xml',
        'wizard/asset_modify_views.xml'
        ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'images': [],
    'summary': 'Asset Depreciation',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: