from odoo import models, fields

class AllocationRejectWizard(models.TransientModel):
    _name = 'allocation.reject.wizard'
    _description = 'Asset Allocation Reject Reason'

    reason = fields.Text(string='Rejection Reason', required=True)
    allocation_id = fields.Many2one('asset.allocation.request', required=True)

    def action_submit_reason(self):
        self.allocation_id.write({
            'state': 'rejected',
            'rejection_reason': self.reason,
        })
        return {'type': 'ir.actions.act_window_close'}