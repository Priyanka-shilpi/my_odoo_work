from odoo import models, fields, api


class CampRoom(models.Model):
    _name = 'camp.room'
    _description = 'Camp Room'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    location = fields.Char("Location")
    asset_ids = fields.Many2many('maintenance.equipment', string='Assets',
                                 domain="[('employee_id', '=', False), ('project_id', '=', False), ('room_id', '=', False), ('state', '=', 'validated'), ('category_id.is_camp_asset', '=', True)]")
    current_occupant_id = fields.Many2one('hr.employee', string='Current Occupant')
    room_type_id = fields.Many2one('camp.room.type', string='Room Type')
    state = fields.Selection([
        ('new', 'New'),
        ('done','Done')], default='new', string='State')
    asset_tags_combined = fields.Text(
        string='Asset Tags',
        compute='_compute_asset_tags_combined',
        store=False,
        required=True
    )
    assigned_asset_ids = fields.One2many('camp.asset.assignment', 'room_id', string='Assigned Assets')
    asset_total_cost = fields.Float(string='Total Asset Cost', compute='_compute_room_costs', store=True)
    room_type_cost = fields.Float(string='Room Type Cost', compute='_compute_room_costs', store=True)
    total_room_cost = fields.Float(string='Total Room Cost', compute='_compute_room_costs', store=True)
    block_id = fields.Many2one('camp.block', string="Block")
    allocation_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], string='Allocation Type')
    occupants_ids = fields.Many2many('hr.employee', string="Employees", readonly=True)
    guest_ids = fields.Many2many('external.employee', string='Guests', readonly=True)
    vacant_slots = fields.Integer(compute='_compute_vacant_slots', store=True)
    occupied_count = fields.Integer(string="Occupied", compute='_compute_occupancy')
    vacant_count = fields.Integer(string="Vacant", compute='_compute_occupancy')
    is_full = fields.Boolean(string="Room Full", compute='_compute_occupancy')
    caravan_id = fields.Many2one('camp.caravan', string="Caravan")
    capacity = fields.Integer(
        string="Room Capacity",
        tracking=True
    )
    hide_done_button = fields.Boolean(compute='_compute_hide_done_button')

    @api.depends('state')
    def _compute_hide_done_button(self):
        for rec in self:
            rec.hide_done_button = rec.state == 'done'

    @api.depends('occupants_ids', 'capacity', 'guest_ids', 'allocation_type')
    def _compute_occupancy(self):
        for room in self:
            if room.allocation_type == 'internal':
                room.occupied_count = len(room.occupants_ids)
            elif room.allocation_type == 'external':
                room.occupied_count = len(room.guest_ids)
            else:
                room.occupied_count = max(len(room.occupants_ids), len(room.guest_ids))
            room.vacant_count = max(room.capacity - room.occupied_count, 0)
            room.is_full = room.occupied_count >= room.capacity

    @api.depends('occupants_ids', 'capacity', 'guest_ids', 'allocation_type')
    def _compute_vacant_slots(self):
        for room in self:
            if room.allocation_type == 'internal':
                room.vacant_slots = max(0, room.capacity - len(room.occupants_ids))
            elif room.allocation_type == 'external':
                room.vacant_slots = max(0, room.capacity - len(room.guest_ids))
            else:
                room.vacant_slots = max(0, room.capacity - len(room.occupants_ids), room.capacity - len(room.guest_ids))

    def notify_user(self):
        for rec in self:
            rec.message_post(
                body=f"@{rec.user_id.name} Please check this record.",
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

    @api.depends('asset_ids', 'asset_ids.product_cost', 'room_type_id.additional_cost')
    def _compute_room_costs(self):
        for rec in self:
            asset_cost = sum(rec.asset_ids.mapped('product_cost'))
            room_type_cost = rec.room_type_id.additional_cost if rec.room_type_id else 0.0
            rec.asset_total_cost = asset_cost
            rec.room_type_cost = room_type_cost
            rec.total_room_cost = asset_cost + room_type_cost

    @api.depends('asset_ids')
    def _compute_asset_tags_combined(self):
        for rec in self:
            tags = rec.asset_ids.mapped('asset_tag_id')
            rec.asset_tags_combined = ', '.join(tag.name for tag in tags if tag.name)

    def action_button_done(self):
        for rec in self:
            if rec.current_occupant_id:
                for asset in rec.asset_ids:
                    asset.employee_id = rec.current_occupant_id.id
            rec.state = 'done'

    @api.model
    def create(self, vals):
        record = super(CampRoom, self).create(vals)
        if record.asset_ids:
            record.asset_ids.write({'room_id': record.id})
        if record.current_occupant_id:
            record.asset_ids.write({'employee_id': record.current_occupant_id.id})
        return record


class CampRoomType(models.Model):
    _name = 'camp.room.type'
    _description = 'Room Type'

    name = fields.Char(required=True)
    additional_cost = fields.Float(string="Additional Room Type Cost")

class CampProcurementRequest(models.Model):
    _name = 'camp.procurement.request'
    _description = 'Procurement Request'

    checklist_line_id = fields.Many2one('camp.asset.checklist.line', string="Checklist Line")
    asset_id = fields.Many2one('maintenance.equipment', string='Asset',domain="[('employee_id', '=', False), ('state', '=', 'validated')]")
    status = fields.Selection([
        ('new', 'New'),
        ('approved', 'Approved'),
        ('done', 'Done'),
    ], default='new', string='Status')
    note = fields.Text(string='Note')
    room_id = fields.Many2one('camp.room', string='Room')
    checklist_id = fields.Many2one('camp.asset.checklist' ,string="Checklist")

class CampAssetTracker(models.Model):
    _name = 'camp.asset.tracker'
    _description = 'Asset Tracker'
    _rec_name = 'asset_id'

    checklist_line_id = fields.Many2one('camp.asset.checklist.line', string="Checklist Line")
    equipment_id = fields.Many2one('camp.equipment', string="Equipment")
    room_id = fields.Many2one('camp.room', string="Room")
    date = fields.Date(string="Transfer Date", default=fields.Date.today)
    transferred_by = fields.Many2one('res.users', string="Transferred By")
    asset_id = fields.Many2one('maintenance.equipment', string='Asset',domain="[('employee_id', '=', False), ('state', '=', 'validated')]")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    status = fields.Selection([
        ('ok', 'OK'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged'),
    ], default='ok', required=True)


