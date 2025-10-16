from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError, AccessError

class  Recurringworkschedule(models.Model):
    _name = 'work.schedule'
    _description = 'Recurring work schedule'

    name = fields.Char(string='Recurring Type')
    days = fields.Float(string='Recurring Days')
