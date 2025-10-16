{
    "name": "Delivery Management",
    "author": "Durga",
    "version": "18.0",
    "license": "LGPL-3",
    "depends": ['base', 'account', ],

    'assets': {
        'web.assets_backend': [
            'delivery_management/static/src/css/custom_delivery_button.css',
        ],
    },

    "data":
        [
            "security/ir.model.access.csv",
            "security/security.xml",
            "wizard/assign_delivery_wizard.xml",
            "views/delivery_assigned.xml",
            "views/delivery_boy.xml",
            "views/delivery_invoices.xml",
            "views/menu.xml",
        ]

}
