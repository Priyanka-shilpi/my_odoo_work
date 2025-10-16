from odoo import models,fields,api


class Class(models.Model):
    _name = "academic.room"
    _rec_name = "name"

    name= fields.Char(string="Name", tracking=True)
