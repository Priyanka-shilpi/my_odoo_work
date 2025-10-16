from odoo import models, fields

class Syllabus(models.Model):
    _name = 'academic.syllabus'

    # class_name = fields.Selection([
    #     ('class one', 'Class One'),
    #     ('class two', 'Class Two'),
    #     ('class three', 'clas Three')
    # ], string='Class')
    class_number=fields.Many2one("academic.class","Class")
    section = fields.Selection(
        [("A","A"),("B", "B"),("C","C")] ,string ="Section")

    def create_syllabus(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Syllabus',
            'res_model': 'academic.syllabusdetails',
            'view_mode': 'form',
            'target': 'new',

        }

    # def filter_syllabus(self):
    #     domain = []
    #     if self.class_namess:
    #         domain.append(('class_names', '=', self.class_names))
    #     if self.section:
    #         domain.append(('section', '=', self.section))

    def filter_syllabus(self):
        # Check if 'default_class_name' is in the context
        class_namess = self.env.context.get('default_class_namess')
        domain = []
        if class_namess:
            domain.append(('class_number', '=', class_namess))  # Filter by class_name in 'academic.subject'

        return {
        'type': 'ir.actions.act_window',
        'name': 'Filtered Syllabus',
        'res_model': 'academic.syllabusdetails',
        'view_mode': 'list',
        'domain': domain,
        'target': 'current',
    }
