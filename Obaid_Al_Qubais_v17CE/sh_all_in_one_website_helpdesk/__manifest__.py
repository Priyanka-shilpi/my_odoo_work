# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "All In One Website Helpdesk | CRM Helpdesk | Sale Order Helpdesk | Purchase Helpdesk | Invoice Helpdesk | Helpdesk Timesheet | Helpdesk Support Ticket To Task | Website Helpdesk",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Website",
    "license": "OPL-1",
    "summary": "Flexible HelpDesk Customizable Help Desk Service Desk HelpDesk With Stages Help Desk Ticket Management Helpdesk Email Templates Helpdesk Chatter Sale Order With Helpdesk Purchase Order With Helpdesk Invoice With Helpdesk SLA Helpdesk Email all in one helpdesk Odoo",
    "description": """Are you looking for fully flexible and customizable helpdesk at website? Our this apps almost contain everything you need for Service Desk, Technical Support Team, Issue Ticket System which include service request to be managed in Odoo backend. Support ticket will send by email to customer and admin. Website customer helpdesk support Ticketing System is used to give the customer an interface where he/she can send support ticket requests and attach documents from the website. Customer can view their ticket from the website portal and easily see the stage of the reported ticket also customers get a link of the portal in email as well. Customer can view their ticket from the website portal and easily see stage of the reported ticket. This desk is fully customizable clean and flexible.""",
    "version": "0.0.1",
    "depends": [
        "sh_all_in_one_helpdesk",
        "web",
        "website",
    ],
    "application": True,
    "data": [
        "data/sh_website_helpdesk_menu.xml",
        "views/website_config_setting_view.xml",
        "views/sh_helpdesk_website_template.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'sh_all_in_one_website_helpdesk/static/src/js/sh_all_in_one_website_helpdesk.js',
            'sh_all_in_one_website_helpdesk/static/src/css/sh_all_in_one_website_helpdesk.css',
        ],
    },

    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": "50",
    "currency": "EUR"
}
