

from odoo import api, models, modules,fields


class Users(models.Model):
    _inherit = 'res.partner'

    agent_is= fields.Boolean("Agent")