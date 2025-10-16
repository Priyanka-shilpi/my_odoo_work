from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class AllocationTransfer(models.TransientModel):
    _name = 'allocation.return.transfer.wizard'
    _description = "Allocation Return Transfer Wizard"

    employee_id = fields.Many2one('hr.employee',string='Assinge To',required=True)

    def action_create_transfer(self):
        active_id = self.env.context.get('active_id')
        original_record = self.env['allcation.request'].browse(active_id)
        new_record = original_record.copy({
            'assing_to': self.employee_id.id,
            'allocation_id':active_id,
            'transfer':True,
        })
        # new_record.make_picking_out()
        original_record.state = "trans"
        return new_record

