from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ITAssetChecklist(models.Model):
    _name = 'it.asset.checklist'
    _description = 'IT Asset Checklist'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Checklist Reference", readonly=True, required=True, copy=False, default='New')
    employee_id = fields.Many2one('hr.employee', required=True, string="Employee")
    project_id = fields.Many2one('project.project', string="Project")
    allocation_id = fields.Many2one('it.asset.allocation', string="Allocation Reference")
    line_ids = fields.One2many('it.asset.checklist.line', 'checklist_id', string="Checklist Lines")
    status = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('escalated', 'Escalated'),
        ('reset', 'Reset'),
    ], default='pending', readonly=True, required=True)
    signed_document = fields.Binary(string='Signed Checklist')
    signed_filename = fields.Char(string='Filename')
    verified_by = fields.Many2one('res.users')
    verified_date = fields.Date()
    show_verify_button = fields.Boolean(compute='_compute_show_verify_button')
    # assignment_id = fields.Many2one(
    #     'it.asset.allocation',
    #     string='Linked Allocation')
    checklist_type = fields.Selection([
        ('allocation', 'Allocation'),
        ('return', 'Return')
    ], string="Checklist Type", default="allocation", required=True)
    remarks = fields.Text('Remarks')

    def print_checklist(self):
        self.ensure_one()
        return self.env.ref('pways_equipment_all_in_one.report_it_asset_checklist_action').report_action(self)


    @api.depends('status')
    def _compute_show_verify_button(self):
        for record in self:
            record.show_verify_button = record.status == 'pending'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals['checklist_type'] == 'allocation':
                vals['name'] = self.env['ir.sequence'].next_by_code('it.asset.allocation.checklist') or 'New'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('it.asset.return.checklist') or 'New'
        checklist = super().create(vals)
        return checklist

    def validate_against_allocation(self):
        for rec in self:
            if not rec.allocation_id:
                continue
            allocated_asset_ids = rec.allocation_id.line_ids.mapped('asset_id.id')
            checklist_asset_ids = rec.line_ids.mapped('asset_id.id')
            missing = list(set(allocated_asset_ids) - set(checklist_asset_ids))
            if missing:
                raise ValidationError("Checklist is missing some allocated assets.")

    def escalate_missing_or_damaged(self):
        Procurement = self.env['camp.procurement.request']
        for line in self.line_ids.filtered(lambda l: l.status in ['missing', 'damaged']):
            # Procurement.create({
            #     'asset_id': line.asset_id.id,
            #     'employee_id': self.employee_id.id,
            #     'note': f"IT Asset {line.status}",
            #     'checklist_id': self.id,
            # })
            line.asset_id.state = 'missing' if line.status == 'missing' else 'damaged'

    def action_verify(self):
        for rec in self:
            if not rec.signed_document:
                raise ValidationError("Signed checklist must be uploaded before verification.")

            if any(not line.status for line in rec.line_ids):
                raise ValidationError("All checklist lines must have a status.")

            rec.validate_against_allocation()

            if any(line.status in ['missing', 'damaged'] for line in rec.line_ids):
                rec.status = 'escalated'
                rec.escalate_missing_or_damaged()
            else:
                rec.status = 'verified'

            rec.verified_by = self.env.user
            rec.verified_date = fields.Date.today()
            rec.message_post(body=f"Checklist verified by {rec.verified_by.name} on {rec.verified_date}.")

    def action_reset(self):
        for rec in self:
            rec.status = 'pending'
            rec.verified_by = False
            rec.verified_date = False
            rec.message_post(body="Checklist reset to editable state.")


class ITAssetChecklistLine(models.Model):
    _name = 'it.asset.checklist.line'
    _description = 'IT Asset Checklist Line'
    _rec_name = 'asset_id'

    checklist_id = fields.Many2one('it.asset.checklist', string="Checklist")
    asset_id = fields.Many2one('maintenance.equipment', string="IT Asset", required=True ,domain="[('employee_id', '=', False), ('state', '=', 'validated')]")
    status = fields.Selection([
        ('ok', 'OK'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged'),
    ], default='ok', required=True)
    description = fields.Text(string="Description")
    asset_tag_id = fields.Many2one('asset.tag.master', related='asset_id.asset_tag_id', store=True, string='Asset Tag')
    serial_number = fields.Char(string="Serial No", readonly=True)
    remarks = fields.Text("Remarks")
    cost = fields.Float(string="Cost")


