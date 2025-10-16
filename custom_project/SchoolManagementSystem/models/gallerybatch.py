from odoo import models, fields

class GalleryBatch(models.Model):
    _name = 'alumini.gallery.batch'
    _description = 'Gallery Batch Reunion'

    name = fields.Char("name", required=True)
    description = fields.Text("Description")
    file = fields.Binary(  string="Images")
