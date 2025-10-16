from odoo import models, fields


from datetime import date

class TakeAttendance(models.Model):
    _name = 'academic.takeattendance'




    # class_name = fields.Selection([
    #     ('class one', 'Class One'),
    #     ('class two', 'Class Two'),
    #     ('class three', 'clas Three')
    # ], string='Class')
    class_namess = fields.Many2one("academic.class","Class")
    section = fields.Selection(
        [("A", "A"), ("B", "B"), ("C", "C")], string="Section")
    date = fields.Date(string="Date")
    student=fields.Many2one("school.student","Student")
    attendance = fields.Selection([("Present","Present"),("Absent","Absent")],string="Attendance")





    def action_save_attendance(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_attendance(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'academic.takeattendance',
            'view_mode': 'form',
            'target': 'current',

        }