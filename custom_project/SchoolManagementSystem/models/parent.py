
from odoo import models,fields,api
from odoo.exceptions import UserError



class Parents(models.Model):
    _name = "users.parents"
    _rec_name = "parent_name"


    parent_id= fields.Char(string="S.no", readonly=True, copy=False, default='New')
    parent_image = fields.Binary(string="Parent Image")
    parent_name = fields.Char( string="Parent Name", tracking=True)
    email = fields.Char(string="Email")
    phone_number = fields.Char(string="Phone Number")
    student = fields.Many2many(comodel_name="school.student", string="Student")

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            # Check if the email ends with '@gmail.com'
            if record.email and not record.email.endswith('@gmail.com'):
                raise UserError("Enter a valid email.The email must end with '@gmail.com'.")

    @api.constrains('phone_number')
    def _check_mobile_number(self):
        for record in self:
            # Check if the student_number is exactly 10 digits long and contains only digits
            if record.phone_number:
                if len(record.phone_number) != 10 or not record.phone_number.isdigit():
                    raise UserError("The mobile number must be exactly 10 digits and contain no characters.")

    @api.model
    def create(self, vals):  # for s_no: 0001
        count = self.search_count([]) + 1
        vals['parent_id'] = str(count).zfill(4)
        return super().create(vals)