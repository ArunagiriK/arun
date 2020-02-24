{
    'name': "Kreol Product Custom",
    'summary': """
       product customization for kreol. 
        """,
    'description': """
     add article field
     add product information
    """,
    'author': 'Codeware/Niyas',
    'website': 'www.codewareuae.com',
    'category': 'Product',
    'version': '12.0.0.0',
    'depends': ['product'],
    'data': [
        'views/product_view.xml',
        'security/ir.model.access.csv',

    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
}
