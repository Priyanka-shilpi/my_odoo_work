from odoo import models, fields

class SaleOrder(models.Model):

    _inherit = "sale.order"
    access = fields.Boolean(string='Access')
