from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = "purchase.order.line"

    image_1920 = fields.Image(string="Image")

    @api.onchange('product_id')
    def onchange_sake_product_image(self):
        for product in self:
            product.image_1920 = product.product_id.image_1920
