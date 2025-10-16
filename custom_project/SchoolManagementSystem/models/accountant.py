from odoo import models,fields,api
from odoo.exceptions import ValidationError



class Accountant(models.Model):
    _name = "users.accountant"
    _rec_name = "accountant_name"

    accountant_id= fields.Char(string="ID", readonly=True, copy=False, default='New')
    accountant_image = fields.Binary(string="Image")
    accountant_name = fields.Char( string="Accountant Name", tracking=True)
    email = fields.Char(string="Email")
    phone_number = fields.Char(string="Phone Number")

    @api.model
    def create(self, vals):  # for s_no: 0001
        count = self.search_count([]) + 1
        vals['accountant_id'] = str(count).zfill(4)
        return super().create(vals)

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and not rec.email.endswith('@gmail.com'):
                raise ValidationError("Email must end with '@gmail.com'.")

    @api.constrains('phone_number')
    def _check_number(self):
        for rec in self:
            if rec.phone_number and not rec.phone_number.isdigit():
                raise ValidationError("Enter a valid number (digits only).")
            if len(rec.phone_number) != 10:
                raise ValidationError("Mobile number must be exactly 10 digits.")
