from odoo import models, fields, api

class AssigningStudentsToDrivers(models.Model):
    _name = 'transport.assignstudents'

    vehicle_model = fields.Many2one('transport.vehiclemodel', string="Vehicle Model", required=True)
    driver_names_id = fields.Many2one('school.drivers', string="Driver")
    section = fields.Selection(
        [("A", "A"), ("B", "B"), ("C", "C")], string="Section")
    student_class_number = fields.Many2one("academic.class", "Class")
    student_name = fields.Many2one("school.student",string='Student')

    def action_save_students(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_students(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'transport.assignstudents',
            'view_mode': 'form',
            'target': 'current',

        }
