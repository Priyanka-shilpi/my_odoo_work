from odoo import models, fields, api
from datetime import time



class FeeManager(models.Model):
    _name = 'accounting.feemanager'
    _rec_name = "students"


    fee_lines=fields.Char("Lines")
    class_name1=fields.Many2one("academic.class","Class")
    date =fields.Date(string="date")
    students = fields.Many2one("school.student",string="Student")

    invoice_title = fields.Char( string='Invoice Title')
    total_amount = fields.Integer(string="Total_amount")
    paid_amount = fields.Integer(string='Paid Amount')
    status = fields.Selection(
        [ ("paid", "Paid"), ("unpaid", "Unpaid")], string="status")


    def action_save_invoice(self):

        return {'type': 'ir.actions.act_window_close'}


    def filter_invoice(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'filter',
            'res_model': 'accounting.feemanager',
            'view_mode': 'form',
            'target': 'current',

        }

