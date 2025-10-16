from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hrmsempid = fields.Integer(string="Employee number")
    vacpreyear = fields.Integer(string="Vacation: Previous Year")
    vaccuryear = fields.Integer(string="Vacation: Current Year")
    usersign = fields.Integer(string="User Signature")
    extempNo = fields.Integer(string="External employee number")
    emp_active = fields.Char(string="Active/inactive status")
    u_emid = fields.Char(string="EmId")


