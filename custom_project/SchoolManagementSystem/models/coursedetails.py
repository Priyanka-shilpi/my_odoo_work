from odoo import models, fields

class CourseDetails(models.Model):
    _name = 'online.coursedetails'

    title = fields.Char(string="Title")
    class_name = fields.Selection([
        ('class one', 'Class One'),
        ('class two', 'Class Two'),
        ('class three', 'clas Three')
    ], string='Class')
    teacher_name = fields.Selection(
        [("priyanka", "Priyanka"), ("Nikhil Varma", "Nikhil Varma"), ("Madhav", "Madhav")], string="Instructor")

    lesson = fields.Integer(string="Lesson")
    total_sections = fields.Integer(string="Total Sections")

    def action_save_details(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_courses(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'online.coursedetails',
            'view_mode': 'form',
            'target': 'current',

        }
