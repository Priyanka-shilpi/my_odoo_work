{
    'name': 'Assets Dashboard',
    'version': '17.0.0.0',
    'depends': ['base', 'web','pways_equipment_all_in_one','maintenance',],
    'data': [
        'security/ir.model.access.csv',
        'security/assets_security.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/chart.js',
            'sdm_assets_dashboard/static/src/js/chart.min.js',
            'sdm_assets_dashboard/static/src/js/assets_dashboard.js',
            'sdm_assets_dashboard/static/src/xml/assets_dashboard.xml',
            'sdm_assets_dashboard/static/src/scss/catalog_style_pdf.scss',

        ],


    },
    'installable': True,
    'application': True,
}
