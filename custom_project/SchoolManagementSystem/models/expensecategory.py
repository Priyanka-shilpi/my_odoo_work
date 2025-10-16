from odoo import models,fields,api


class ExpenseCategory(models.Model):
    _name = "accounting.expense"

    name= fields.Char(string="Name", tracking=True)
