from odoo import models, fields


class SchoolSettings(models.Model):
    _name = 'school.settings'
    _rec_name = "school_name"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    school_name = fields.Char(string="School Name",        related='company_id.name')
    phone = fields.Integer(string='Phone Number')
    address=fields.Char(string="Address")

    def update_settings(self):
        return {'type': 'ir.actions.act_window_close'}
