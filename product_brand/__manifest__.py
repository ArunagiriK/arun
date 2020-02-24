# -*- coding: utf-8 -*-
{
	'name' : 'Product Brand',
	'version' : '1.0',
	'category': 'Product',
	'author': 'Hashmicro/GYB IT SOLUTIONS-Anand',
	'description': """ 	""",
	'website': 'http://www.hashmicro.com/',
	'depends' : [
		'product',
	],
	'data': [
        'security/ir.model.access.csv',
		'views/product.xml',
	    'views/product_brand.xml',
	    'views/product_style.xml',
	],
	'demo': [
	],
	'installable': True,
	'application': True,
	'auto_install': False,
}
