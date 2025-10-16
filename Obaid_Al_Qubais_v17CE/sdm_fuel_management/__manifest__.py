{
    'name': 'Fuel Management',
    'version': '17.0.1.0.0',
    'category': 'Fleet',
    'author': 'Sidmec / Aswin',
    'summary': 'Manage fuel entries and monitor usage',
    'depends': ['fleet', 'hr', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/fuel_entry_views.xml',
        'views/fuel_report_views.xml',
    ],
    'installable': True,
    'application': True,
}
