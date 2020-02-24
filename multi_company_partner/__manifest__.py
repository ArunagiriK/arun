{
    'name': "Multi Company Partner Rule",
    'summary': """
       add a many2many field for company, and partner will be available in all the selected companies. 
        """,
    'description': """
    this module is for add company restriction to Customer/Supplier
    """,
    'author': 'Codeware/Niyas',
    'website': 'www.codewareuae.com',
    'category': 'Base',
    'version': '12.0.0.0',
    'depends': ['base'],
    'data': [
        'views/partner_view.xml',
        'security/security.xml'
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
}
