from odoo import models, fields

class StudentLine(models.Model):
    _name = "student.line"
    _description = "Student Line"

    student_name = fields.Many2one(comodel_name="res.partner", string="Student Name")
    student_email = fields.Char(string="Email")
