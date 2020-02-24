{
    'name': "Product Substitution",
    'summary': """
       Product Substitute. 
        """,
    'description': """
    this module is will give option to add substitute product. we can add it in sale order.
    """,

    'author': 'Codeware/Niyas',
    'website': '',
    'category': 'Product',
    'version': '12.0.0.0',
    'depends': ['product','sale'],
    'data': [
        'wizard/substitute_product_wiz_view.xml',
        'views/sale_view.xml',
        'views/substitute_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
}
