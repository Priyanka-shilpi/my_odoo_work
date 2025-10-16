from odoo import models, fields

class AssignDeliveryWizard(models.TransientModel):
    _name = 'assign.delivery.wizard'
    _description = 'Assign Delivery Wizard'

    transportation = fields.Selection([
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('truck', 'Truck'),
    ], string="Transportation", required=True)

    delivery_boy_id = fields.Many2one('delivery.boy', string='Delivery Boy', required=True)

    def action_assign(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            records = self.env['delivery.management'].browse(active_ids)
            for record in records:
                record.delivery_boy = self.delivery_boy_id.id
                record.write({'delivery_boy': self.delivery_boy_id.id})
        return {'type': 'ir.actions.act_window_close'}
