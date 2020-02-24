{
    'name': "Lock Fiscal Year ",
    'summary': """
          we can schedule date for fiscal year lock for no advisors.
        """,
    'description': """
    """,
    'author': 'Codeware/Niyas',
    'website': 'www.codewareuae.com',
    'category': 'Accouting',
    'version': '12.0.0.0',
    'depends': ['account'],
    'data': [
        'data/period_lock_date_cron.xml',
        'views/res_company_view.xml'
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
}
