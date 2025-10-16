from odoo import models,fields,api


class Class(models.Model):
    _name = "academic.class"
    _rec_name = "class_names"

    class_names= fields.Selection([
        ("X", "X"),
        ("IX", "IX"),
        ("VIII", "VIII"),
        ("VII", "VII"),
        ("VI", "VI"),
        ("V", "V"),
        ("IV", "IV"),
        ("III", "III"),
        ("II", "II"),
        ("I", "I")
    ], string="Class",  tracking=True)
    section = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C")
    ], string="Section",  tracking=True)


