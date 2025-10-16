from odoo import models,fields,api


class Class(models.Model):
    _name = "academic.department"
    _rec_name = "department_name"

    department_name= fields.Char(string="Name", tracking=True)
