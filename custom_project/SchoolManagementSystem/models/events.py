from odoo import models,fields,api

from datetime import date

class Events(models.Model):
    _name = "users.events"
    _rec_name = "event_name"

    event_image = fields.Binary(string="Photo")
    event_name = fields.Char( string="Event Title", tracking=True)
    from_date = fields.Date(string="Start")
    end_date= fields.Date(string="End")
