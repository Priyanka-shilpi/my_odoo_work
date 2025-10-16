from odoo import models, fields, api

class CampClearanceRequest(models.Model):
    _name = 'camp.clearance.request'
    _description = 'Clearance for Transfer/Resignation'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', required=True)
    room_id = fields.Many2one('camp.room', required=True)
    checklist_id = fields.Many2one('camp.asset.checklist')
    clearance_date = fields.Date(default=fields.Date.today)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('deducted', 'Deducted'),
    ], default='pending')
    deduction_line_ids = fields.One2many('camp.deduction.line', 'clearance_id')
    total_deduction = fields.Monetary(string='Total Deduction', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('deduction_line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.total_deduction = sum(line.amount for line in rec.deduction_line_ids)

    def action_process_clearance(self):
        for rec in self:
            deductions = []
            for line in rec.checklist_id.line_ids.filtered(lambda l: l.status in ['damaged', 'missing']):
                asset_value = line.asset_id.value or 0
                deductions.append((0, 0, {
                    # 'asset_id': line.asset_id.id,
                    'status': line.status,
                    'amount': asset_value,
                }))
            if deductions:
                rec.deduction_line_ids = deductions
                rec.state = 'deducted'
            else:
                rec.state = 'cleared'


class CampDeductionLine(models.Model):
    _name = 'camp.deduction.line'
    _description = 'Deduction Detail'

    clearance_id = fields.Many2one('camp.clearance.request')
    asset_id = fields.Many2one('maintenance.equipment')
    status = fields.Selection([
        ('damaged', 'Damaged'),
        ('missing', 'Missing'),
    ])
    amount = fields.Monetary()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    date = fields.Date(default=fields.Date.today)
    description = fields.Char(string='Description')
    request_id = fields.Many2one('maintenance.request', string="Maintenance Request", ondelete='cascade')
    allocation_id = fields.Many2one('allocation.request', ondelete='cascade')
