from odoo import models,fields,api


from datetime import date

class Exam(models.Model):
    _name = "examination.exam"
    _rec_name = "exam_name"

    exam_name= fields.Char(string="Name", tracking=True)
    starting_date = fields.Date(string="Starting Date")
    ending_date = fields.Date(string="Ending Date")

