from odoo import models, fields

class Marks(models.Model):
    _name = 'exam.marks'
    _rec_name = "student_class_number1"


    student_class_number1 = fields.Many2one("academic.class", store=True,string="Standard")

    sections = fields.Selection(
        [("A","A"),("B", "B"),("C","C")] ,string ="Section")

    subject = fields.Selection(
        [("Telugu","Telugu"),("Hindi", "Hindi"),("English","English"),
         ("Maths","Maths"),("Physics","Physics"),("Biology","Biology"),("Social Studies","Social Studies")] ,string ="Subject")


    def allot_marks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': ',Marks',
            'res_model': 'exam.marksdetails',
            'view_mode': 'form',
            'target': 'new',

        }

    def filter_marks(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Filtered Marks',
                'res_model': 'exam.marksdetails',
                'view_mode': 'list,form',
                'domain': [('student_class_number1','=',rec.student_class_number1.id)],
                'target': 'current',
            }


