from odoo import models, fields

class CampCaravan(models.Model):
    _name = 'camp.caravan'
    _description = 'Camp Caravan'

    name = fields.Char(required=True)
    block_id = fields.Many2one('camp.block', string="Block")


class CampCamp(models.Model):
    _name = 'camp.camp'
    _description = 'Camp Master'

    name = fields.Char(required=True)
    location = fields.Char(string='Location')
    block_ids = fields.One2many('camp.block', 'camp_id', string='Blocks')
