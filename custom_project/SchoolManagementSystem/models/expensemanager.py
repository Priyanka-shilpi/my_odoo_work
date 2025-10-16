from odoo import models,fields,api



class ExpenseCategory(models.Model):
    _name = "accounting.manager"
    _rec_name = "names"
    date = fields.Date( string="Date", tracking=True)
    names = fields.Many2one("accounting.expense",  string ="Expense Category")
