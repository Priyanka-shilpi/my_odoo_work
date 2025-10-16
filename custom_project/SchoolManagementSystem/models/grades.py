from odoo import models,fields,api

from datetime import date

class Grades(models.Model):
    _name = "exam.grades"
    _rec_name = "grade"


    grade = fields.Char(string="Grade")
    grade_point = fields.Float(string="Grade Point", tracking=True)
    from_marks= fields.Integer(string="Mark From")
    upto_marks= fields.Integer(string="Mark Upto")
