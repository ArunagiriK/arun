{
    'name': "Asset Pivot View",
    'description': """
        Account asset pivot view
       """,
    'author': "Odoxsofthub",
    'version': '1.0.1',
    'website': "www.odooxsofthub.com",
    'depends': [
        'base','account','account_asset'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/asset_pivot_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}