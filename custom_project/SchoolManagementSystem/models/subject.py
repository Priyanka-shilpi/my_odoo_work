from odoo import models, fields

class Subject(models.Model):
    _name = 'academic.subject'

    name = fields.Char(string="Subject Name")

    standard_names=fields.Many2one("academic.class","Class")

    def add_subjects_for_all_classes(self):
        subjects = [
            "Math",
            "Science",
            "English",
            "Social Studies",
            "Computer Science",
            "Physical Education"
        ]

        classes = [
            "Class One",
            "Class Two",
            "Class Three",
            "Class Four",
            "Class Five",
            "Class Six",
            "Class Seven",
            "Class Eight",
            "Class Nine",
            "Class Ten"
        ]

        for class_name in classes:
            for subject in subjects:
                self.env['academic.subject'].create({
                    'standard_names': class_name,
                    'name': subject
                })

    def add_subject(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subject',
            'res_model': 'academic.subjectlines',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_class_name': self.standard_names,
            }
        }

    def filter_subject(self):
        class_name = self.env.context.get('default_class_name')
        domain = []
        if class_name:
            domain.append(('standard_names', '=', class_name))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Subjects',
            'res_model': 'academic.subject',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }
