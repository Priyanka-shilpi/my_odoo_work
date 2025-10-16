{
    'name': 'Agent Comission',
    'category': 'Sales/Accounting',
    'sequence': 150,
    'version': '17.0.1.0.0',
    'summary': 'Commission for Agents',
    'description': """
               This module gives you a quick view of your commissions to the agents"
    """,
    'depends': ['base', 'mail','sale','account'],
    'data': [
        "security/ir.model.access.csv",
        'views/contact_views.xml',
        "views/sale_order.xml",
        "views/account_move.xml",
        "views/commission.xml",

    ],

    'application': True,
    'license': 'LGPL-3',
}
