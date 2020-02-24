{
    'name': "Product Average LandCost",
    'description': """
        Product Average Landcost
       """,
    'author': "Odoxsofthub",
    'version': '1.0.1',
    'website': "www.odooxsofthub.com",
    'depends': [
        'stock_account', 'stock_landed_costs'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}