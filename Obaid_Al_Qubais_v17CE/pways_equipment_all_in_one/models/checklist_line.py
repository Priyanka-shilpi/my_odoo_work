from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CampAssetChecklist(models.Model):
    _name = 'camp.asset.checklist'
    _description = 'Room Asset Checklist'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    name = fields.Char(string="Checklist Reference", readonly=True, required=True, copy=False, default='New')
    room_id = fields.Many2one('camp.room', required=True)
    employee_id = fields.Many2one('hr.employee', string='Verified For')
    line_ids = fields.One2many('camp.asset.checklist.line', 'checklist_id')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('escalated', 'Escalated'),
        ('reset', 'Reset'),
    ], default='pending',readonly= True, required=True)
    signed_document = fields.Binary(string='Signed Checklist')
    signed_filename = fields.Char(string='Filename')
    verified_by = fields.Many2one('res.users')
    verified_date = fields.Date()
    show_verify_button = fields.Boolean(compute='_compute_show_verify_button')
    checklist_type = fields.Selection([
        ('checkin', 'Check-In'),
        ('checkout', 'Check-Out')
    ], default='checkin', required=True, string="Checklist Type")
    remarks = fields.Text(string='Remarks')
    assignment_id = fields.Many2one('camp.asset.assignment', string='Linked Assignment')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals['checklist_type'] == 'checkin':
                vals['name'] = self.env['ir.sequence'].next_by_code('camp.rooms.allocation.checklist') or 'New'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('camp.rooms.return.checklist') or 'New'
        checklist = super().create(vals)
        return checklist

    @api.depends('status')
    def _compute_show_verify_button(self):
        for record in self:
            record.show_verify_button = record.status == 'pending'

    def validate_against_asset_register(self):
        for rec in self:
            if not rec.room_id.room_type_id:
                continue
            template = self.env['camp.asset.template'].search([
                ('room_type_id', '=', rec.room_id.room_type_id.id)
            ], limit=1)
            expected_assets = template.asset_ids.ids if template else []
            actual_assets = rec.line_ids.mapped('asset_id.id')
            missing = list(set(expected_assets) - set(actual_assets))
            if missing:
                raise ValidationError("Checklist does not match expected assets for this room.")

    def escalate_to_procurement(self):
        Procurement = self.env['camp.procurement.request']
        for line in self.line_ids.filtered(lambda l: l.status in ['missing', 'damaged']):
            Procurement.create({
                'asset_id': line.asset_id.id,
                'room_id': self.room_id.id,
                'note': line.status,
                'checklist_id': self.id,
            })
            line.asset_id.state = 'missing' if line.status == 'missing' else 'damaged'

    def action_reset(self):
        for rec in self:
            rec.status = 'pending'
            rec.verified_by = False
            rec.verified_date = False
            rec.message_post(body="Checklist has been reset and is now editable again.")

    def log_asset_transfer(self):
        Tracker = self.env['camp.asset.tracker']
        today = fields.Date.today()

        for line in self.line_ids:
            existing_log = Tracker.search([
                ('asset_id', '=', line.asset_id.id),
                ('room_id', '=', self.room_id.id),
                ('employee_id', '=', self.employee_id.id),
                ('date', '=', today),
            ], limit=1)

            if existing_log:
                existing_log.write({
                    'status': line.status,
                })
            else:
                Tracker.create({
                    'asset_id': line.asset_id.id,
                    'room_id': self.room_id.id,
                    'employee_id': self.employee_id.id,
                    'date': today,
                    'status': line.status,
                })

    def action_verify(self):
        for rec in self:
            if not rec.signed_document:
                raise ValidationError("Signed checklist must be uploaded before verification.")

            for line in rec.line_ids:
                if not line.status:
                    raise ValidationError("All checklist items must have a status before verification.")
            rec.validate_against_asset_register()

            if any(line.status in ['missing', 'damaged'] for line in rec.line_ids):
                rec.status = 'escalated'
                rec.escalate_to_procurement()
            else:
                rec.status = 'verified'

            rec.verified_by = self.env.user
            rec.verified_date = fields.Date.today()

            rec.log_asset_transfer()

            rec.message_post(body=f"Checklist verified by {rec.verified_by.name} on {rec.verified_date}.")

    def print_checklist(self):
        self.ensure_one()
        report_action = self.env.ref('pways_equipment_all_in_one.report_camp_asset_checklist_action')
        return report_action.report_action(self)


class CampAssetChecklistLine(models.Model):
    _name = 'camp.asset.checklist.line'
    _description = 'Checklist Asset Line'
    _rec_name = 'asset_id'

    checklist_id = fields.Many2one(
        'camp.asset.checklist',
        string="Checklist",
        required=True,
        ondelete='cascade'
    )
    description = fields.Char(string='Description')
    checklist_ids = fields.Char(string='Title/Name')
    asset_id = fields.Many2one('maintenance.equipment', required=True,domain="[('employee_id', '=', False), ('state', '=', 'validated')]")
    status = fields.Selection([
        ('ok', 'OK'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged'),
    ], default='ok', required=True)
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    asset_tag_id = fields.Many2one('asset.tag.master', related='asset_id.asset_tag_id', store=True, string='Asset Tag')
    serial_no = fields.Char(related='asset_id.lot_id.name', readonly=True)
    remarks = fields.Text(string="Remarks")
    cost = fields.Float(string="Cost", related='asset_id.product_cost')


class CampAssetTemplate(models.Model):
    _name = 'camp.asset.template'
    _description = 'Camp Asset Template'

    name = fields.Char(string="Template Name")
    room_type_id = fields.Many2one('camp.room.type', string='Room Type')
