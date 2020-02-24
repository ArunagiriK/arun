{
    'name': "Partner Terms",
    'description': """
        Partner terms Calculation based on several terms
       """,
    'author': "Odoxsofthub",
    'version': '1.0.1',
    'website': "www.odooxsofthub.com",
    'category': 'Sales and Invoicing',
    'depends': [
        'base','account','partner_company_group','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_terms.xml',
        'views/term_calculation.xml',
        'views/product_views.xml',
        'data/scheduled_action.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}