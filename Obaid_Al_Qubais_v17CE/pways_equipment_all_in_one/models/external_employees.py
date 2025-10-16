from odoo import fields, models


class ExternalEmployee(models.Model):
    _name = 'external.employee'
    _description = 'External Employee'

    name = fields.Char(string='Name', required=True)
    phone = fields.Char(string='Phone', required=True)
    id_proof = fields.Binary(string='ID Proof', required=True)