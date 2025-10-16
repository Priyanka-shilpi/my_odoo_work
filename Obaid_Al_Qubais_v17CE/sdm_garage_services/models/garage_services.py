from odoo import models, fields, api

class GarageVehicleService(models.Model):
    _name = 'garage.vehicle.service'
    _description = 'Vehicle Service & Breakdown Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'vehicle_id'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    in_timestamp = fields.Datetime(string='IN Timestamp', required=True)
    out_timestamp = fields.Datetime(string='OUT Timestamp')
    service_description = fields.Text(string='Service Description')
    wrench_time = fields.Float(string='Wrench Time (hrs)', compute='_compute_wrench_time', store=True)
    status = fields.Selection([
        ('in_service', 'In Service'),
        ('completed', 'Completed'),
        ('external_repair', 'Out for External Repair')
    ], string='Service Type', default='in_service')

    def action_set_complete(self):
        self.status = 'completed'

    def action_set_repair(self):
        self.status = 'external_repair'

    @api.depends('in_timestamp', 'out_timestamp')
    def _compute_wrench_time(self):
        for record in self:
            if record.in_timestamp and record.out_timestamp:
                delta = record.out_timestamp - record.in_timestamp
                record.wrench_time = delta.total_seconds() / 3600.0
            else:
                record.wrench_time = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('garage.vehicle.service') or 'New'
        return super().create(vals)


class GarageConsumableUsage(models.Model):
    _name = 'garage.consumable.usage'
    _description = 'Consumables & Spare Parts Usage'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    usage_date = fields.Date(string='Date', default=fields.Date.context_today)
    item_id = fields.Many2one('product.product', string='Item', required=True)
    quantity = fields.Float(string='Quantity Used', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    usage_reason = fields.Text(string='Usage Reason')


class GarageConsumableReport(models.Model):
    _name = 'garage.consumable.report'
    _auto = False
    _description = 'Monthly Consumables Report'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    item_id = fields.Many2one('product.product', string='Item')
    total_quantity = fields.Float(string='Total Quantity')
    month = fields.Char(string='Month')

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW garage_consumable_report AS (
                SELECT
                    MIN(id) as id,
                    vehicle_id,
                    item_id,
                    SUM(quantity) as total_quantity,
                    TO_CHAR(usage_date, 'YYYY-MM') as month
                FROM garage_consumable_usage
                GROUP BY vehicle_id, item_id, TO_CHAR(usage_date, 'YYYY-MM')
            )
        """)
