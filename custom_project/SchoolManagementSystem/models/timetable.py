from odoo import models, fields


from datetime import time

class TimeTable(models.Model):
    _name = 'academic.timetable'



    class_id = fields.Many2one(comodel_name="academic.class"
                              , string='Class')
    day = fields.Char(string='Day')
    # class_name = fields.Selection([
    #     ('class one', 'Class One'),
    #     ('class two', 'Class Two'),
    #     ('class three', 'clas Three')
    # ], string='Class')
    # #
    section = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C')
    ], string='Section')
    name = fields.Many2one(comodel_name="academic.subject"
                                 , string='Subject')
    teacher_name = fields.Many2one(comodel_name="hr.employee"
                              , string='Teacher')
    class_room = fields.Many2one(comodel_name="academic.room"
                                   , string='Class Room')

    starting_hour = fields.Datetime(string='Starting Hour')
    ending_hour = fields.Datetime(string='Ending  Hour')

    def action_save_routine(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_routine(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'academic.timetable',
            'view_mode': 'form',
            'target': 'current',

        }
