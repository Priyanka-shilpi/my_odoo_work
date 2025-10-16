from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='Related product for this invoice line',
    )