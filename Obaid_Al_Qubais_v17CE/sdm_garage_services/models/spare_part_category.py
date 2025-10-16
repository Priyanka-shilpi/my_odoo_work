from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SparePartCategory(models.Model):
    _name = 'spare.part.category'
    _description = 'Spare Part Category'
    _rec_name = 'name'

    name = fields.Char(string="Category Name", required=True)
    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
