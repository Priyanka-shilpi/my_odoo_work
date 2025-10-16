from odoo import models, fields

class OnlineCourses(models.Model):
    _name = 'online.course'
    _rec_name = "status"

    class_names=fields.Many2one("academic.class","Class")
    teacher_name = fields.Selection(
        [("priyanka","Priyanka"),("Nikhil Varma", "Nikhil Varma"),("Madhav","Madhav")] ,string ="Instructor")

    status = fields.Selection(
        [("active","Active"),("inactive", "In Active"),] ,string ="Status")


    def create_new_course(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Online Course',
            'res_model': 'online.coursedetails',
            'view_mode': 'form',
            'target': 'new',
        }

    def filter_courses(self):
        domain = []
        if self.class_name:
            domain.append(('class_name', '=', self.class_name))
        if self.teacher_name:
            domain.append(('teacher_name', '=', self.teacher_name))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Courses',
            'res_model': 'online.coursedetails',
            'view_mode': 'list',
            'domain': domain,
            'target': 'current',
        }
