{
    'name': "Multi Company Product Rule",
    'summary': """
       add a many2many field for company, and product will be available in all the selected companies. 
        """,
    'description': """
    this module is for add company restriction to product
    """,
    'author': 'Codeware/Niyas',
    'website': 'www.codewareuae.com',
    'category': 'Product',
    'version': '12.0.0.0',
    'depends': ['product'],
    'data': [
        'views/product_view.xml',
        'security/security.xml',

    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
}
