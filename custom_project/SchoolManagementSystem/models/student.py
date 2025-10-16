from odoo import models, fields


class Student(models.Model):
   _name = 'school.student'
   _description = 'Student'
   _rec_name = "name"


   name = fields.Char(string="Name")
   email = fields.Char(string="Email")
   password = fields.Char(string="Password")
   parent_id = fields.Many2one('res.partner', string="Parent")
   student_class_number1=fields.Many2one("academic.class","Class")
   section = fields.Selection([
       ("A", "A"),
       ("B", "B"),
       ("C", "C")
   ], string="Section")
   dob = fields.Datetime(string="Date of Birth")
   gender = fields.Selection([
       ("male", "Male"),
       ("female", "Female")
   ], string="Gender")
   blood_group = fields.Selection([
   ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
       ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-")
   ], string="Blood Group")
   address = fields.Char(string="Address")
   mobile_number = fields.Char(string="Mobile Number")
   image = fields.Binary(string="Profile Image")

