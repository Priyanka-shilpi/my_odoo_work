from odoo import api, fields, models

class OwnershipType(models.Model):
    _name = 'ownership.type'
    _rec_name = 'name'

    name = fields.Char(string="Ownership Type")

