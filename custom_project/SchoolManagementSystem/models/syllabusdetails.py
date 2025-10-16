from odoo import models, fields


from datetime import time

class SyllabusDetails(models.Model):
    _name = 'academic.syllabusdetails'




    # class_name = fields.Selection([
    #     ('class one', 'Class One'),
    #     ('class two', 'Class Two'),
    #     ('class three', 'clas Three')
    # ], string='Class')
    class_namess = fields.Many2one("academic.class","Class")
    section = fields.Selection(
        [("A", "A"), ("B", "B"), ("C", "C")], string="Section")
    title = fields.Char(string="Title")
    subjects = fields.Many2one("academic.subject",string='Subject')
    upload_syllabus = fields.Binary(string="Upload Syllabus")





    def action_save_syllabus(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_syllabus(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'academic.syllabusdetails',
            'view_mode': 'form',
            'target': 'current',

        }
