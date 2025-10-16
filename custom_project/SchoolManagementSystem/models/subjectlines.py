from odoo import models, fields

class SubjectLines(models.Model):
    _name = 'academic.subjectlines'


    class_names=fields.Many2one("academic.class","Class")
    subject_ids = fields.Many2many('academic.subject', string='Subjects')

    def action_save_subject(self):
        return {'type': 'ir.actions.act_window_close'}

    def filter_subject(self):
        domain = []
        if self.class_names:
            domain.append(('standard_names', '=', self.class_name))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Subjects',
            'res_model': 'academic.subjectlines.line',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }

    def default_get(self, fields):
        res = super().default_get(fields)
        if 'default_class_names' in self.env.context:
            res['class_names'] = self.env.context['default_class_names']
        return res
