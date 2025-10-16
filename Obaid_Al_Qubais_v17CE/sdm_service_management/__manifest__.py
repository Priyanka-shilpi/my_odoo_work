{
    'name': 'Fleet Supply Management',
    'version': '1.0',
    'depends': ['fleet','sdm_trip_management'],
    'category': 'Fleet',
    'author': 'Aswin/Sidmec',
    'summary': 'Manage Gatch Supply services within Fleet',
    'description': 'Adds Gatch Supply entry and service type management under Fleet.',
    'data': [
        'security/ir.model.access.csv',
        'reports/report_gatch_supply.xml',
        'reports/report.xml',
        'data/sequence.xml',
        'views/service_type_views.xml',
        'views/gatch_supply_views.xml',
    ],
    'installable': True,
    'application': False,
}