from odoo import models,fields,api

from datetime import date

class ManageAlumini(models.Model):
    _name = "alumini.manage"
    _rec_name = "alumini"

    alumini = fields.Many2one("school.student","Name")
    image=fields.Binary(string="photo")
    student_code = fields.Char(string="Student code")
    email= fields.Char(string="Email")
    phone_number= fields.Char(string = "Phone Number")
    passing_session= fields.Selection([("2017","2017"),("2018","2018"),("2019","2019"),("2020","2020")],string = "Passing Session")
    profession= fields.Char(string = "Profession")
    # file = fields.Binary(string="Upload  File")




