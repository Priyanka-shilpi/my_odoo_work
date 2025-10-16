# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Custom Contacts',
    'category': 'Sales/CRM',
    'sequence': 150,
    'version': '18.0.1.0.0',
    'summary': 'Centralize your address book',
    'description': """
        This module gives you a quick view of your contacts directory, accessible from your home page.
        You can track your vendors, customers and other contacts.
    """,
    'depends': ['base', 'mail'],
    'data': [
        'views/contact_views.xml',
    ],
    'demo': [
        'data/mail_demo.xml',
    ],
    'application': True,
    'license': 'LGPL-3',
}
