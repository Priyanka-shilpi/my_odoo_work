from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime



class delivery_collection(models.Model):
    _name = 'delivery.collection'
    _description = 'Delivery Collection'

    delivery_id = fields.Many2one('delivery.management', string="Delivery Reference", required=True)
    amount_residual = fields.Monetary(string="Due Amount", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)


    # def action_collect_delivery(self):
    #     for record in self:
    #         if record.amount_residual != 0:
    #             # Update the related delivery's state
    #             if record.delivery_id:
    #                 record.delivery_id.delivery_state = 'collection'
    #         else:
    #             raise UserError("Amount residual is zero; nothing to collect.")