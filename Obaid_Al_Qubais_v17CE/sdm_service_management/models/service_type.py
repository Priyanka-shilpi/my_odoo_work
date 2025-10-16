from odoo import models, fields


class ServiceType(models.Model):
    _name = 'gatch.service.type'
    _description = 'Service Type'
    _rec_name = 'name'

    name = fields.Char(required=True)
