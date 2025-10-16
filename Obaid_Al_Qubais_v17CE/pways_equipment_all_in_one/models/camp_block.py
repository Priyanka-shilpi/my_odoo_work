from odoo import models, fields, api

class CampBlock(models.Model):
    _name = 'camp.block'
    _description = 'Camp Block'

    name = fields.Char(required=True)
    camp_id = fields.Many2one('camp.camp', string="Camp", required=True)
    caravan_count = fields.Integer(string="No. of Caravans")
    room_ids = fields.One2many('camp.room', 'block_id', string="Rooms")

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    religion = fields.Char(string="Religion")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', ('name', operator, name), ('barcode', operator, name)]
        employees = self.search(domain + args, limit=limit)
        return employees.name_get()

    def name_get(self):
        result = []
        for emp in self:
            name = emp.name
            if emp.barcode:
                name += f" [{emp.barcode}]"
            result.append((emp.id, name))
        return result

