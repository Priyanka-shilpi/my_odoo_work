{
	'name': "Product Image On Purchase Order Line",
	'version': "17.0.0.0",
	'category': "Purchase",
	'license':'LGPL-3',
	'summary': "Display product image in Purchase order line print product image in Purchase  order report.",
	'description': """ Displaying product image in purchase order line and also in purchase order report.""",
	'author': "SIDMEC",
    'depends': ['base', 'purchase'],
	'data': [
			'views/view_purchase_order.xml',
			],
	'installable': True,
	'auto_install': False,
	'application': False,
}
