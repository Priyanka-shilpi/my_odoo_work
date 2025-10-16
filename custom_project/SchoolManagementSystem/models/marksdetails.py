from odoo import models, fields,api


from datetime import time

class SyllabusDetails(models.Model):
    _name = 'exam.marksdetails'
    _rec_name = "name"

    name = fields.Many2one("school.student", string='Student Name' ,domain=[('student_class_number1','!=',False)])
    marks_id = fields.Many2one("exam.marks", string="Marks Reference")
    marks = fields.Integer(string="Marks")
    grade = fields.Char(string="Grade", compute="_compute_grade")
    grade_point = fields.Float(string="Grade Point", compute="_compute_grade")
    comment = fields.Char(string="Comment")
    student_class_number1 = fields.Many2one("academic.class","Class",related="name.student_class_number1")
    sections = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C")
    ], string="Section",store=True)
    subject_ids = fields.Many2one("academic.subject", string="Subject")  # 🆕 Add this
    def action_save_marks(self):
        vals = {
            'name': self.name.id,
            'marks': self.marks,
            'grade_point': self.grade_point,
            'comment': self.comment,
            'marks_id': self.marks_id.id,
        }
        self.env['exam.marksdetails'].create(vals)

        return {'type': 'ir.actions.act_window_close'}

    def filter_marks(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'exam.marksdetails',
            'view_mode': 'form',
            'target': 'current',

        }

    @api.depends('marks')
    def _compute_grade(self):
        for rec in self:
            grade_obj = self.env['exam.grades'].search([
                ('from_marks', '<=', rec.marks),
                ('upto_marks', '>=', rec.marks)
            ], limit=1)

            rec.grade = grade_obj.grade if grade_obj else ''
            rec.grade_point = grade_obj.grade_point if grade_obj else 0.0