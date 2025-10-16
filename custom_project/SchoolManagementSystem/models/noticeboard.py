from odoo import models,fields,api


class Notice(models.Model):
    _name = "back.notice"
    _rec_name = "notice_name"

    notice_name= fields.Char(string="Notice Title", tracking=True)
    date = fields.Date(string="Date")
    photo = fields.Binary(string="Notice Photo")
