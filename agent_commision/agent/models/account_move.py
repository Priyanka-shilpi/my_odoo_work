from odoo import api, models, modules,fields
from odoo.exceptions import UserError


class Users(models.Model):
    _inherit = 'account.move'

    commission_id=fields.Integer("Commission Id")
    status=fields.Selection([('paid','Paid'),('not_paid','Not Paid')],"status")
    agents=fields.Many2one("res.partner","Agent")
    invoice_id=fields.Many2one("account.move","Invoice")
    partner =fields.Many2one("res.partner","Customer")



    commission_amount = fields.Float(string="Commission Amount")


    def action_confirm_commission(self):
        self.ensure_one()
        if not self.agents:
            raise UserError("Please select an agent before confirming commission.")

        commission = self.env['agent.commission'].create({
            'invoice_id': self.id,
            'agent': self.agents.id,
            'commission_amount': self.commission_amount,
        })

        return {
            'name': 'Agent Commission',
            'view_mode': 'form',
            'res_model': 'agent.commission',
            'res_id': commission.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
