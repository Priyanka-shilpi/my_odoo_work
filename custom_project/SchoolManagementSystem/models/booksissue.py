from odoo import models, fields

class BooksIssue(models.Model):
    _name = 'back.book'

    date= fields.Date(string="Date")

    def issue_book(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'add book',
            'res_model': 'back.issue',
            'view_mode': 'form',
            'target': 'new',

        }

    def filter_books(self):
        domain = []
        if self.date:
            domain.append(('date', '=', self.date))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Books',
            'res_model': 'back.issue',
            'view_mode': 'list',
            'domain': domain,
            'target': 'current',
        }

