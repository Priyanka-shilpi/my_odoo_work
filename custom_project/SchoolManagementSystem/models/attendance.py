from odoo import models, fields
from datetime import date


class Attendance(models.Model):
    _name = 'academic.attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "month"
    month=fields.Selection([("January","January"),
                            ("Febraury","Febraury"),
                            ("March","March"),
                            ("April","April"),
                            ("May","May"),
                            ("June","June"),
                            ("July","July"),
                            ("August","August"),
                            ("September","September"),
                            ("October","October"),
                            ("November","November"),
                            ("December","December")],string="Month")
    year=fields.Selection([("1","2019"),("2","2020"),("3","2021"),("4","2022"),("5","2023"),("6","2024"),("7","2025")],string="Year")
    class2=fields.Many2one("academic.class","Class")
    section = fields.Selection(
        [("A","A"),("B", "B"),("C","C")] ,string ="Section")

    def take_attendance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance',
            'res_model': 'academic.takeattendance',
            'view_mode': 'form',
            'target': 'new',
        }


    def filter_attendance(self):
        class_namess = self.env.context.get('default_class_namess')
        domain = []
        if class_namess:
            domain.append(('class2', '=', class_namess))

        return {
        'type': 'ir.actions.act_window',
        'name': 'Filtered Attendance',
        'res_model': 'academic.takeattendance',
        'view_mode': 'list',
        'domain': domain,
        'target': 'current',
    }