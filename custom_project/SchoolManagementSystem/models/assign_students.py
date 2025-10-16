from odoo import models, fields,api

class AssignStudents(models.Model):
    _name = 'transport.assign'
    _rec_name = "category"

    category =fields.Selection([('driver','Driver'),('class','Class'),('vehicle','Vehicle')])
    vehicle_model = fields.Many2one('transport.vehiclemodel', string="Vehicle Model")
    student_class_number = fields.Many2one('academic.class', string="Class")
    driver_names_id = fields.Many2one('school.drivers', string="Driver")

    def assign_student(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Student',
            'res_model': 'transport.assignstudents',
            'view_mode': 'form',
            'target': 'new',
        }

    def filter(self):
        domain = []
        if self.category == 'vehicle' and self.vehicle_model:
            domain.append(('vehicle_model', '=', self.vehicle_model.id))
        elif self.category == 'class' and self.student_class_number:
            domain.append(('student_class_number', '=', self.student_class_number.id))
        elif self.category == 'driver' and self.driver_names_id:
            domain.append(('driver_names_id', '=', self.driver_names_id.id))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Students',
            'res_model': 'transport.assignstudents',
            'view_mode': 'list',
            'domain': domain,
            'target': 'current',
        }
