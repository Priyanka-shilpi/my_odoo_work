from odoo import models, fields, api


class VehicleModel(models.Model):
    _name = 'transport.vehiclemodel'
    _rec_name = 'name'

    name = fields.Char(string='Model Name', required=True)


