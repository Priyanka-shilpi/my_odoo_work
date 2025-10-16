{
    'name': 'SDM  Report Customization',
    'version': '17.0.0.0',
    'depends': ['product', 'account','sale_management','sale'],
    'summary': 'Added new report format in invoice',
    'data': [
        'views/custom_report.xml',
        'views/report_template.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
