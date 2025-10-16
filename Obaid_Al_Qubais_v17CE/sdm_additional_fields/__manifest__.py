{
    'name': 'SDM Additional Fields',
    'version': '17.0.0.0',
    'category': 'Sales/CRM',
    'author': 'Sidmec / vishnu',
    'website': '',
    'depends': ['base', 'sale', 'crm', 'purchase_stock', 'stock', 'hr', 'fleet'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_fleet_expiry_check.xml',
        'views/hr_employee_view.xml',
        'views/ownership_type.xml',
        'views/fleet_vehicle_view.xml',
        'views/res_config_settings_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}