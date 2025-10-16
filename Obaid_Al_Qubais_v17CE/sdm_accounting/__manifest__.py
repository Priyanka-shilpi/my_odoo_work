# -*- coding: utf-8 -*-

{
    'name': 'Sidmec Accounting',
    'category': 'Accounting/Accounting',
    'author': "SIDMEC",
    'summary': 'Manage financial and analytic accounting',
    'summary': 'Accounting Reports, Asset Management and Budget, Recurring Payments, '
             'Lock Dates, Fiscal Year, Accounting Dashboard, Financial Reports, '
               'Customer Follow up Management, Bank Statement Import',
    'description': 'Odoo 17 Financial Reports, Asset Management and '
                   'Budget, Financial Reports, Recurring Payments, '
                   'Bank Statement Import, Customer Follow Up Management,'
                   'Account Lock Date, Accounting Dashboard',
    'website': 'https://www.sidmectech.com/',
    'support': 'support@sidmectech.com',
    'depends': ['account', 'web_tour'],
    'data': [
        'data/account_accountant_data.xml',
        'data/ir_cron.xml',
        'data/digest_data.xml',

        'security/ir.model.access.csv',
        'security/account_accountant_security.xml',

        'views/account_account_views.xml',
        'views/account_fiscal_year_view.xml',
        'views/account_journal_dashboard_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/account_reconcile_views.xml',
        'views/account_reconcile_model_views.xml',
        'views/account_accountant_menuitems.xml',
        'views/digest_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/bank_rec_widget_views.xml',

        'wizard/account_change_lock_date.xml',
        'wizard/account_auto_reconcile_wizard.xml',
        'wizard/account_reconcile_wizard.xml',
        'wizard/reconcile_model_wizard.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'sdm_accounting/static/src/js/tours/accounting.js',
            'sdm_accounting/static/src/components/**/*',
            'sdm_accounting/static/src/**/*.xml',
        ],
        'web.assets_tests': [
            'sdm_accounting/static/tests/tours/**/*',
        ],
        'web.qunit_suite_tests': [
            'sdm_accounting/static/tests/*.js',
            'sdm_accounting/static/tests/helpers/*.js',
        ],
    }
}
