from odoo import models, fields, api
from odoo.exceptions import UserError


from datetime import date


class Admission(models.Model):
    _name = "school.admission"
    _rec_name = "student"

    student = fields.Char( string="Student Name", tracking=True)
    student_email = fields.Char(string="Email", tracking=True)
    student_password = fields.Char(string="Password", password=True)
    parent = fields.Many2one(comodel_name="users.parents", string="Parent", tracking=True)
    student_class_number1 = fields.Many2one("academic.class", store=True, string="Standard")
    student_section_ABC = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C")], string="Section", tracking=True)
    student_dob = fields.Datetime(string="Date of Birth", tracking=True)
    student_age = fields.Integer(string="Age", compute="_compute_age", store=True)
    student_gender = fields.Selection([("male", "Male"), ("female", "Female")], string="Gender", tracking=True)
    student_blood_group = fields.Selection([
        ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-")
    ], string="Blood group", tracking=True)
    student_address = fields.Char(string="Address")
    student_number = fields.Char(string="Mobile Number")
    student_image = fields.Binary(string="Student Profile Image")

    def single_student_admission(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Driver',
            'res_model': 'school.admission',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_student_id': self.id
            }
        }

    def bulk_student_admission(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bulk Student Admission',
            'res_model': 'bulk.student.admission',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_student_id': self.id
            }
        }

    @api.model
    def create(self, vals):
        admission = super().create(vals)

        self.env['school.student'].create({
            'name': admission.student,
            'email': admission.student_email,
            'password': admission.student_password,
            'parent_id': admission.parent.id if admission.parent else False,
            'student_class_number1': admission.student_class_number1.id,
            'section': admission.student_section_ABC,
            'dob': admission.student_dob,
            'gender': admission.student_gender,
            'blood_group': admission.student_blood_group,
            'address': admission.student_address,
            'mobile_number': admission.student_number,
            'image': admission.student_image,
        })

        return admission

    @api.constrains('student_email')
    def _check_email(self):
        for record in self:
            # Check if the email ends with '@gmail.com'
            if record.student_email and not record.student_email.endswith('@gmail.com'):
                raise UserError("Enter a valid email.The email must end with '@gmail.com'.")

    @api.constrains('student_number')
    def _check_mobile_number(self):
        for record in self:
            # Check if the student_number is exactly 10 digits long and contains only digits
            if record.student_number:
                if len(record.student_number) != 10 or not record.student_number.isdigit():
                    raise UserError("The mobile number must be exactly 10 digits and contain no characters.")

    @api.depends('student_dob')
    def _compute_age(self):
        for record in self:
            if record.student_dob:
                today = date.today()
                birth_date = record.student_dob.date() if isinstance(record.student_dob,
                                                                     date) else record.student_dob
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                record.student_age = age
            else:
                record.student_age = 0


