from odoo import api, models, modules,fields


class Users(models.Model):
    _inherit = 'sale.order'

    any_agent = fields.Boolean("Any Agent?")
    agent=fields.Many2one("res.partner","Agent", domain="[('agent_is', '=', True)]")
    list_price=fields.Many2one("product.template","")


    commission= fields.Selection([('fix','Fix') ,('per','Percent')],"Commission Type")

    fix=fields.Integer("Fix")
    per=fields.Float("Percentage")
    commission_amount = fields.Float(string="Commission Amount", compute="_compute_commission_amount")

    @api.depends('order_line.price_subtotal', 'per', 'fix', 'commission', 'order_line')
    def _compute_commission_amount(self):
        for order in self:
            if order.commission == 'fix':
                order.commission_amount = order.fix
            elif order.commission == 'per':
                order.commission_amount = (order.amount_untaxed * order.per) / 100.0
            else:
                order.commission_amount = 0.0

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({
            'agents':self.agent.id,
            'commission_amount': self.commission_amount,
        })
        return vals




