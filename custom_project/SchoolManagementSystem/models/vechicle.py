from odoo import models,fields,api
from odoo.exceptions import ValidationError
import re


class Drivers(models.Model):
    _name = "transport.vehicle"
    _rec_name = "vehicle_model"

    vehicle_s_no = fields.Char(string="S.no", readonly=True, copy=False, default='New')
    # number = fields.Integer(string="S.No")
    vh_number = fields.Char(string="vehicle Number")
    # vh_model = fields.Char(string="vehicle Model")
    # vh_model = fields.Selection(
    #     selection=[
    #         ('car', 'Car'),
    #         ('bus', 'Bus'),
    #         ('van', 'Van'),
    #         ('other', 'Other'),
    #     ],
    #     string="Vehicle Model",
    #     required=True,
    # )

    vehicle_model = fields.Many2one('transport.vehiclemodel', string="Vehicle Model", required=True)


    capacity = fields.Float(string="Capacity")
    # route = fields.Char(string="Route")
    route_id = fields.Many2one('transport.route', string="Route name")
    vehicle_image = fields.Binary(string="Upload Image")


    @api.model
    def create(self, vals):      #for s_no: 0001
        count = self.search_count([]) + 1
        vals['vehicle_s_no'] = str(count).zfill(4)
        return super().create(vals)


    @api.constrains('vh_number')
    def _check_vehicle_number(self):
        pattern = r'^[A-Z]{2} \d{2} [A-Z]{2} \d{4}$'
        for rec in self:
            if rec.vh_number and not re.match(pattern, rec.vh_number):
                raise ValidationError("Vehicle number must be in format: 'TS 10 EQ 0297'")


    # def action_create_vehicle(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Create Driver',
    #         'res_model': 'transport.vehicle',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_vehicle_id': self.id
    #         }
    #     }

    def action_create_route(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Route',
            'res_model': 'transport.route',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_start_point': 'Enter Start',
                'default_end_point': 'Enter End',
            }
        }


