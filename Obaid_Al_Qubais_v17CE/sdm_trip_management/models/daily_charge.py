from odoo import fields, models, _

class DailyCharge(models.Model):
    _name = 'daily.charge'
    _description = 'Daily Trip Charges'
    _rec_name = 'trip_id'

    trip_id = fields.Many2one('trip.management', string='Trip Reference', required=True, ondelete='cascade')
    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    plate_id = fields.Many2one(related='trip_id.plate_id', string='Vehicle', store=True)
    charge_date = fields.Date(string='Charge Date', required=True, default=fields.Date.today)
    cost_type = fields.Selection([
        ('fuel', 'Fuel'),
        ('maintenance', 'Maintenance'),
        ('toll', 'Toll'),
        ('other', 'Other'),
    ], string='Cost Type', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)