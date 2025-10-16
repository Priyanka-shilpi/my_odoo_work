from odoo import models, fields


from datetime import time

class Issue(models.Model):
    _name = 'back.issue'
    _rec_name = "student_name"

    date = fields.Date(string='Issue Date')
    student_name = fields.Many2one(comodel_name="school.student",string="student")
    class_number = fields.Many2one(comodel_name="academic.class" , string="Class", tracking=True)
    book_name =fields.Char(string="Book")

    def action_save_book_issue(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_issue(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'back.issue',
            'view_mode': 'form',
            'target': 'current',
        }
