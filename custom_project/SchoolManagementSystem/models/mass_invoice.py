from odoo import models, fields


from datetime import time

class FeeManager(models.Model):
    _name = 'accounting.massinvoice'

    class_names=fields.Many2one("academic.class","Class")
    section = fields.Char(string="Section")
    date =fields.Date(string="date")

    invoice_title = fields.Char( string='Invoice Title')
    total_amount = fields.Integer(string="Total_amount")
    paid_amount = fields.Integer(string='Paid Amount')
    status = fields.Selection(
        [("All status", "All Status"), ("paid", "Paid"), ("unpaid", "Unpaid")], string="status")


    def action_save_invoice(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_invoice(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'accounting.massinvoice',
            'view_mode': 'form',
            'target': 'current',

        }