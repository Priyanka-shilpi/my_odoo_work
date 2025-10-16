from odoo import models, fields, api


class BulkStudentAdmission(models.Model):
   _name = 'bulk.student.admission'
   _description = 'Bulk Student Admission'
   _rec_name = 'id'


   name = fields.Char(string="Reference", required=True, default="New")
   admission_line_ids = fields.One2many('bulk.student.admission.line', 'admission_id', string='Students')


   def action_confirm_bulk_admission(self):
       student_model = self.env['school.student']
       # student_vals_list = []
       for admission in self:
           for line in admission.admission_line_ids:
               student_model.create({
                   'name': line.name.name,
                   'student_class_number1': line.student_class_number1.id,
                   'section': line.section,
                   'email': line.email,
                   'password': line.password,
                   'gender': line.gender,
                   'parent_id': line.parent_id.id,
               })
           self.unlink()


class BulkStudentAdmissionLine(models.Model):
    _name = 'bulk.student.admission.line'
    _description = 'Bulk Student Admission Line'

    admission_id = fields.Many2one('bulk.student.admission', string='Admission Reference')
    student_class_number1 = fields.Many2one("academic.class", store=True, string="Standard")

    # class_number = fields.Selection([
    #     ("Class Ten", "Class Ten"),
    #     ("Class Nine", "Class Nine"),
    #     ("Class Eight", "Class Eight"),
    #     ("Class Seven", "Class Seven"),
    #     ("Class Six", "Class Six"),
    #     ("Class Five", "Class Five"),
    #     ("Class Four", "Class Four"),
    #     ("Class Three", "Class Three"),
    #     ("Class Two", "Class Two"),
    #     ("Class One", "Class One")
    # ], string="Class", tracking=True)
    section = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C")], "Section", tracking=True, )
    names = fields.Many2one(comodel_name="school.student", string="Student Name", tracking=True)
    email = fields.Char(string="Email")
    password = fields.Char(string="Password", password=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    parent_ids = fields.Many2one(comodel_name="users.parents",string="Parent")
