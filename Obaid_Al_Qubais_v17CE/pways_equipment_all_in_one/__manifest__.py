# -*- coding: utf-8 -*-
{
    'name': 'HR Equipment ALL in ONE',
    'version': '17.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """ 
            Equipment allocation and return or transfer to employees and equipment maintenance process includes following features
            Create allocation request and link equipment with product and serial
            Equipment request approvals
            Allocation and return or transfer
            Create Equipment Maintenance
            Add multiple components and create stock movements
            Create invoices for Maintenance
            Auto create Maintenance request based on define recurring days
            Skip request on employee weekend or holidays
            Equipment Maintenance
            Repair Maintenance
            Vehicle Maintenance
            Maintenance request 
            Auto Maintenance request 
            HR Equipment
            Repair Order
            Maintenance Request
            Equipment Allocation
            Employee Equipment allocation
        """,

    'depends': ['purchase_stock', 'hr_maintenance', 'maintenance', 'account', 'project_timesheet_holidays', 'mail', 'om_account_asset'],
    'author': 'Preciseways',
    'data': [
        'data/data.xml',
        'data/email_data.xml',
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'reports/camp_asset_checklist_report.xml',
        'wizard/transfer_view.xml',
        'wizard/asset_scrap_wizard_view.xml',
        'wizard/reject_reason_wizard_view.xml',
        'views/external_employees.xml',
        'views/maintenance_request_views.xml',
        'views/it_asset_checklist_views.xml',
        'views/tools_asset_checklist_views.xml',
        'views/asset_tag_master_views.xml',
        'views/maintenance_equipment_inherit.xml',
        'views/recurring_work_schedule_view.xml',
        'views/allocation_request.xml',
        'views/checklist_line.xml',
        'views/product_inherit.xml',
        'views/asset_allocation_view.xml',
        'views/camp_views.xml',
        'views/it_asset_allocation_views.xml',
    ],
    'installable': True,
    'application': True,
    'price': 31.0,
    'currency': 'EUR',
    'images': ['static/description/banner.png'],
    'license': 'OPL-1',
}
