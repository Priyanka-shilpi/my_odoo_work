from odoo import models,fields,api


class Teachers(models.Model):
    _inherit ="hr.employee"
    # _rec_name = "teacher_name"

    # teacher_image = fields.Binary(string="Image")
    # teacher_name = fields.Char( string="Teacher Name", tracking=True)
    # department = fields.Char(string="Department", tracking=True)
    # designation = fields.Char(string="Designation")
    # phone_number = fields.Char(string="Phone Number")
    #
    #
    # def action_create_teacher(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Create Teacher',
    #         'res_model': 'users.teachers',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_teacher_id': self.id
    #         }
    #     }
