from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class schooltransportdrivers(models.Model):
    _name = "school.drivers"
    _rec_name = "driver_name"

    driver_image = fields.Binary(string="Upload Image")
    driver_s_no = fields.Char(string="S.no", readonly=True, copy=False, default='New')
    driver_name = fields.Char(string="Driver Name", tracking=True, required=True)
    driver_email = fields.Char(string="Email", tracking=True, required=True)
    driver_number = fields.Char(string="Mobile Number")
    driver_vehicle_number = fields.Char(string="Vehicle Number")

    @api.model
    def create(self, vals):      #for s_no: 0001
        count = self.search_count([]) + 1
        vals['driver_s_no'] = str(count).zfill(4)
        return super().create(vals)

    @api.constrains('driver_email')
    def _check_email(self):
        for rec in self:
            if rec.driver_email and not rec.driver_email.endswith('@gmail.com'):
                raise ValidationError("Email must end with '@gmail.com'.")

    @api.constrains('driver_number')
    def _check_driver_number(self):
        for rec in self:
            if rec.driver_number and not rec.driver_number.isdigit():
                raise ValidationError("Enter a valid number (digits only).")
            if len(rec.driver_number) != 10:
                raise ValidationError("Mobile number must be exactly 10 digits.")

    @api.constrains('driver_vehicle_number')
    def _check_vehicle_number(self):
        pattern = r'^[A-Z]{2} \d{2} [A-Z]{2} \d{4}$'
        for rec in self:
            if rec.driver_vehicle_number and not re.match(pattern, rec.driver_vehicle_number):
                raise ValidationError("Vehicle number must be in format: 'TS 10 EQ 0297'")

