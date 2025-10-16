from odoo import api, models, modules,fields


class Users(models.Model):
    _name = 'agent.commission'

    partner_id =fields.Many2one("res.partner","Customer")
    invoice_id=fields.Many2one("account.move","Invoice")
    currency_id =fields.Many2one("account.move","Currency")
    commission_amount = fields.Float(string="Commission Amount")
    agent=fields.Many2one("res.partner","Agent", domain="[('agent_is', '=', True)]")

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    commission_amount = fields.Float(string='Commission Amount')


