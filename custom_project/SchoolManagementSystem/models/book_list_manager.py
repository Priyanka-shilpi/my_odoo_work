from odoo import models,fields,api


class Book(models.Model):
    _name = "library.book"
    _rec_name = "book_name"

    book_name= fields.Char(string="Book Name", tracking=True)
    author= fields.Char(string="Author", tracking=True)
    copy = fields.Char(string="Number of Copies", tracking=True)
