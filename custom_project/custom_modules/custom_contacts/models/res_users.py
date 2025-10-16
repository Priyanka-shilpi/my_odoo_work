# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, modules,fields


class Users(models.Model):
    _inherit = 'res.partner'

    access= fields.Boolean("Access")

    # @api.model
    # def systray_get_activities(self):
    #     """ Update the systray icon of res.partner activities to use the
    #     contact application one instead of base icon. """
    #     activities = super(Users, self).systray_get_activities()
    #     for activity in activities:
    #         if activity['model'] != 'res.partner':
    #             continue
    #         activity['icon'] = modules.module.get_module_icon('contacts')
    #     return activities
