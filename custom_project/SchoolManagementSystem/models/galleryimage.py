from odoo import models, fields

class GalleryImage(models.Model):
    _name = 'alumini.gallery.image'
    _description = 'Gallery Images'

    name = fields.Char("Caption")
    image = fields.Image("Image")
