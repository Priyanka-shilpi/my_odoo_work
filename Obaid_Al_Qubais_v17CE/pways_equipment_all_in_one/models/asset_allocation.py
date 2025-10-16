from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AllocationRequest(models.Model):
    _name = 'asset.allocation.request'
    _description = 'Asset Allocation Request'
    _rec_name = 'asset_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    asset_id = fields.Many2one(
        'maintenance.equipment',
        string='Asset/Vehicle',
        required=True,
        domain="[('employee_id', '=', False), ('project_id', '=', False), ('room_id', '=', False), ('state', '=', 'validated'), ('category_id.is_asset', '=', True)]"
    )
    employee_id = fields.Many2one('hr.employee', string='Allocated To (Employee)')
    # allocation_type = fields.Selection([
    #     ('internal', 'Internal'),
    #     ('external', 'External')
    # ], string='Allocated To (Project)')
    allocation_date = fields.Date(string='Allocation Date', default=fields.Date.today, required=True)
    location = fields.Char(string='Location')
    returned_date = fields.Date(string='Returned Date')
    state = fields.Selection([
        ('new', 'New'),
        ('created', 'Created'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('allocated', 'Allocated'),
        ('returned', 'Returned'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='new', tracking=True)
    category_id = fields.Many2one('account.asset.category', "Asset Category",related='asset_id.category_id',store=True, required=True)
    request_id = fields.Many2one('allcation.request', string="Request Reference")
    asset_tag_id = fields.Many2one('asset.tag.master', related='asset_id.asset_tag_id', store=True, string='Asset Tag')
    employee_barcode = fields.Char(
        string="Employee ID",
        related='employee_id.barcode',
        store=True,
        readonly=True
    )
    project_id = fields.Many2one('project.project', string='Allocated To (Project)')
    # _sql_constraints = [
    #     ('unique_employee_barcode', 'unique(employee_barcode)', 'The employee barcode must be unique!')
    # ]
    company_id = fields.Many2one('res.company', string="Company")
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        if self.asset_id:
            self.category_id = self.asset_id.category_id

    def notify_user(self):
        for rec in self:
            rec.message_post(
                body=f"@{rec.user_id.name} Please check this record.",
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

    def action_notify_manager(self):
        for rec in self:
            rec.message_post(
                body="Reminder: Allocation requires manager attention.",
                subject="Asset Allocation Reminder",
                message_type="notification",
            )
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                summary='Follow-up on Allocation',
                user_id=rec.create_uid.id,
            )

    @api.constrains('project_id', 'employee_id', 'company_id')
    def _check_allocation_validations(self):
        for rec in self:
            if not rec.employee_id and not rec.project_id:
                raise ValidationError("Either Employee or Project must be selected.")

            if not rec.company_id:
                raise ValidationError("Company must be selected.")

            if rec.project_id == 'internal' and rec.employee_id and rec.employee_id.company_id != rec.company_id:
                raise ValidationError(
                    "For Internal allocation, the selected employee must belong to the selected company.")

    @api.onchange('employee_id')
    def _onchange_employee_or_project(self):
        if self.employee_id:
            self.company_id = self.employee_id.company_id

    @api.constrains('employee_id', 'project_id')
    def _check_allocation_target(self):
        for rec in self:
            if not rec.employee_id and not rec.project_id:
                raise ValidationError("You must allocate the asset to either an Employee or a Project.")
            if rec.employee_id and rec.project_id:
                raise ValidationError(
                    "You cannot allocate an asset to both an Employee and a Project at the same time.")

    @api.model
    def create(self, vals):
        if vals.get('asset_id') and not vals.get('category_id'):
            asset = self.env['maintenance.equipment'].browse(vals['asset_id'])
            if asset.category_id:
                vals['category_id'] = asset.category_id.id

        if vals.get('state') == 'approved':
            existing = self.search([
                ('asset_id', '=', vals['asset_id']),
                ('state', '=', 'allocated')
            ])
            if existing:
                raise ValidationError("This asset has already been allocated and cannot be selected again.")

        return super(AllocationRequest, self).create(vals)

    def action_submit(self):
        for rec in self:
            if rec.asset_id.is_expensive:
                rec.state = 'pending'
                rec.message_post(
                    body=f"Asset '{rec.asset_id.name}' is marked as Expensive. Request moved to Pending Approval.",
                    subtype_xmlid="mail.mt_note"
                )
                rec.notify_approvers()
            else:
                rec.state = 'created'
                rec.message_post(
                    body=f"Asset '{rec.asset_id.name}' allocation submitted successfully without approval.",
                    subtype_xmlid="mail.mt_note"
                )

    def notify_approvers(self):
        group = self.env.ref('maintenance.group_equipment_manager', raise_if_not_found=False)
        template = self.env.ref('pways_equipment_all_in_one.email_template_equipment_approval',
                                raise_if_not_found=False)

        if not group or not template:
            _logger.warning("Approval group or email template not found.")
            return

        users = self.env['res.users'].search([('groups_id', 'in', group.id)])
        for user in users:
            self.message_post(
                body=f"Approval request sent to {user.name} ({user.email}).",
                subtype_xmlid="mail.mt_note"
            )
            template.with_context(
                lang=user.lang or 'en_US',
                tz=user.tz or 'UTC',
                default_model=self._name,
                default_res_id=self.id,
            ).send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': user.email,
                    'recipient_ids': [(6, 0, [user.partner_id.id])]
                }
            )

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'allocation.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_allocation_id': self.id,
            }
        }

    def action_pending(self):
        for rec in self:
            rec.state = 'pending'

    def action_allocate(self):
        for rec in self:
            if rec.state != 'approved':
                raise ValidationError("Only approved requests can be allocated.")

            if rec.asset_id.employee_id:
                raise ValidationError("This asset is already allocated to '%s'" % rec.asset_id.employee_id.name)
            if rec.employee_id:
                rec.asset_id.employee_id = rec.employee_id
            else:
                rec.asset_id.employee_id = False

            if rec.project_id:
                rec.asset_id.project_id = rec.project_id
            else:
                rec.asset_id.project_id = False
            if rec.location:
                rec.asset_id.location = rec.location

            rec.state = 'allocated'

    def action_return(self):
        for rec in self:
            rec.returned_date = fields.Date.today()
            rec.state = 'returned'
            if rec.employee_id:
                rec.asset_id.employee_id = False
            if rec.location:
                rec.asset_id.location = False

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

class ProjectProject(models.Model):
    _inherit = 'project.project'

    equipment_ids = fields.One2many('maintenance.equipment', 'project_id', string="Assets")
    equipment_count = fields.Integer(string="Asset Count", compute="_compute_equipment_count")

    def _compute_equipment_count(self):
        for rec in self:
            rec.equipment_count = len(rec.equipment_ids)

    def action_project_equipment_assets(self):
        self.ensure_one()
        return {
            'name': 'Project Assets',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.equipment',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }



class CampAssetAssignment(models.Model):
    _name = 'camp.asset.assignment'
    _description = 'Room Assignment Request'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: ('New'))
    allocation_type = fields.Selection([('internal', 'Internal'),
                                        ('external', 'External')],
                                       required=True, string='Allocation Type')
    room_id = fields.Many2one('camp.room', required=True,
                              domain=[('state', '=', 'done'), ('vacant_slots', '>', 0)])
    employee_id = fields.Many2one('hr.employee', string='Employee')
    allocation_date = fields.Date(string='Allocation Date', default=fields.Date.today, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Check-In'),
        ('return', 'Check-Out'),
    ], default='draft')
    assigned_assets_in_room = fields.Many2many(
        'maintenance.equipment',
        related='room_id.asset_ids',
        string="Assets in Selected Room",
    )
    employee_barcode = fields.Char(
        string="Employee ID",
        related='employee_id.barcode',
        store=True,
        readonly=True
    )
    # _sql_constraints = [
    #     ('unique_employee_barcode', 'unique(employee_barcode)', 'The employee barcode must be unique!')
    # ]
    total_room_asset_cost = fields.Float(
        string="Total Room Asset Cost",
        related='room_id.asset_total_cost',
        store=False,
        readonly=True
    )
    project_id = fields.Many2one('project.project', string="Allocated To (Project)")
    company_id = fields.Many2one('res.company', string="Company", related='employee_id.company_id')
    checkin_checklist_id = fields.Many2one(
        'camp.asset.checklist',
        string="Check-In Checklist",
        domain=[('checklist_type', '=', 'checkin')]
    )
    checkout_checklist_id = fields.Many2one(
        'camp.asset.checklist',
        string="Check-Out Checklist",
        domain=[('checklist_type', '=', 'checkout')]
    )
    consumable_ids = fields.Many2many('product.product', string='Consumables',
                                      domain=[('detailed_type', '=', 'consu')])
    external_employee_id = fields.Many2one('external.employee', string='External Employee')
    external_contact_id = fields.Many2one('res.partner', string='External Company')

    def _validate_allocation_type_conflict(self):
        """
        Validates that the room's existing allocation type (internal/external) is not in conflict
        with the current assignment. Prevents mixing internal employees and external guests in the same room.
        """
        for rec in self:
            room_type = rec.room_id.allocation_type
            if rec.allocation_type == 'internal' and room_type == 'external':
                raise ValidationError(
                    "This room is currently assigned to external guests.\n"
                    "You cannot mix internal employees and external guests in the same room."
                )
            elif rec.allocation_type == 'external' and room_type == 'internal':
                raise ValidationError(
                    "This room is currently assigned to internal employees.\n"
                    "You cannot mix external guests and internal employees in the same room."
                )
            else:
                rec.room_id.allocation_type = rec.allocation_type

    def _validate_duplicate_checkin(self):
        """
        Checks for any duplicate active check-ins for the same employee or guest.
        Prevents assigning an employee/guest to multiple rooms at the same time.
        """
        for rec in self:
            domain = [('id', '!=', rec.id), ('state', '=', 'assigned')]
            if rec.allocation_type == 'internal' and rec.employee_id:
                domain += [('employee_id', '=', rec.employee_id.id)]
                duplicate = self.env['camp.asset.assignment'].search(domain, limit=1)
                if duplicate:
                    raise ValidationError(
                        f"{rec.employee_id.name} is already checked in to Room {duplicate.room_id.name}.")
            elif rec.allocation_type == 'external' and rec.external_employee_id:
                domain += [('external_employee_id', '=', rec.external_employee_id.id)]
                duplicate = self.env['camp.asset.assignment'].search(domain, limit=1)
                if duplicate:
                    raise ValidationError(
                        f"{rec.external_employee_id.name} is already checked in to Room {duplicate.room_id.name}.")

    def _validate_room_capacity(self):
        """
        Validates if the room is full. Prevents allocation to a room that has reached its capacity.
        """
        for rec in self:
            if rec.room_id.is_full:
                raise ValidationError(f"Room {rec.room_id.name} is currently full. Please choose another room.")

    def _validate_checklist(self, checklist, assigned_assets):
        """
        Ensures that a valid and verified checklist exists and that its assets
        exactly match the currently assigned assets.
        """
        if not checklist:
            raise ValidationError("Check-in checklist is missing. Please create and verify it before proceeding.")
        if checklist.status == 'pending':
            raise ValidationError("Check-in checklist is pending verification. Please verify it before proceeding.")
        checklist_assets = sorted(checklist.line_ids.mapped('asset_id.id'))
        assigned_asset_ids = sorted(assigned_assets.ids)
        if checklist_assets != assigned_asset_ids:
            raise ValidationError("Mismatch between checklist assets and assigned assets. Please ensure they match.")

    def action_assign(self):
        """
        Main method to assign a room and assets to an employee or guest.
        Performs all necessary validations and updates related fields accordingly.
        """
        for rec in self:
            if not rec.assigned_assets_in_room:
                raise ValidationError("Please assign assets before proceeding with room allocation.")

            rec._validate_allocation_type_conflict()
            rec._validate_duplicate_checkin()
            rec._validate_room_capacity()
            rec._validate_checklist(rec.checkin_checklist_id, rec.assigned_assets_in_room)

            for asset in rec.assigned_assets_in_room:
                if asset.state != 'validated':
                    raise ValidationError(
                        f"Asset-{asset.name} is not Validated Assets.\nOnly Validated Assets can be allocated.")
                asset.room_id = rec.room_id
                asset.external_contact_id = rec.external_contact_id

            rec.room_id.current_occupant_id = rec.employee_id
            if rec.allocation_type == 'internal' and rec.room_id.allocation_type != 'external':
                rec.room_id.occupants_ids = [(4, rec.employee_id.id)]
            elif rec.allocation_type == 'external' and rec.room_id.allocation_type != 'internal':
                rec.room_id.guest_ids = [(4, rec.external_employee_id.id)]

            rec.state = 'assigned'

    def action_return(self):
        """
        Marks an assignment as returned. Verifies the check-out checklist and clears
        room and asset associations with the employee or guest.
        """
        for rec in self:
            checklist = rec.checkout_checklist_id
            if not checklist:
                raise ValidationError("Check-Out checklist is missing. Please create and verify it before proceeding.")
            if checklist.status == 'pending':
                raise ValidationError("Check-Out checklist is pending verification. Please verify it before proceeding.")

            for asset in rec.assigned_assets_in_room:
                asset.room_id = False
                asset.external_contact_id = False

            rec.room_id.current_occupant_id = False

            if rec.allocation_type == 'internal' and rec.room_id.allocation_type != 'external':
                rec.room_id.occupants_ids = [(3, rec.employee_id.id)]
            elif rec.allocation_type == 'external' and rec.room_id.allocation_type != 'internal':
                rec.room_id.guest_ids = [(3, rec.external_employee_id.id)]

            if not rec.room_id.occupants_ids and not rec.room_id.guest_ids:
                rec.room_id.allocation_type = False

            rec.state = 'return'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('camp.rooms.allocation') or 'New'
        return super().create(vals)

    def create_checklist(self, checklist_type):
        """
        Creates a new checklist (check-in or check-out) with the assigned assets
        and populates the checklist lines with relevant details.
        """
        checklist = self.env['camp.asset.checklist'].create({
            'employee_id': self.employee_id.id,
            'room_id': self.room_id.id,
            'assignment_id': self.id,
            'checklist_type': checklist_type,
        })
        checklist_lines = [{
            'checklist_id': checklist.id,
            'asset_id': asset.id,
            'serial_no': asset.lot_id.name or '',
            'cost': asset.product_cost or 0.0,
            'status': 'ok',
        } for asset in self.assigned_assets_in_room]
        self.env['camp.asset.checklist.line'].create(checklist_lines)
        return checklist

    def update_checklist(self, checklist, extra_assets):
        """
        Adds new (missing) assets to an existing checklist. Used when assigned assets
        are updated after the checklist was first created.
        """
        lines = [{
            'checklist_id': checklist.id,
            'asset_id': asset.id,
            'serial_no': asset.lot_id.name or '',
            'cost': asset.product_cost or 0.0,
            'status': 'ok',
        } for asset in extra_assets]
        self.env['camp.asset.checklist.line'].create(lines)

    def action_open_checkin_checklist(self):
        """
        Opens the check-in checklist for review. Creates or updates it as needed and
        ensures all validation checks are passed before opening.
        """
        self.ensure_one()
        if not self.assigned_assets_in_room:
            raise ValidationError("Please assign assets before proceeding.")

        self._validate_allocation_type_conflict()
        self._validate_duplicate_checkin()
        self._validate_room_capacity()

        for asset in self.assigned_assets_in_room:
            if asset.state != 'validated':
                raise ValidationError(f"Asset-{asset.name} is not Validated Assets.\nOnly Validated Assets can be allocated.")

        if not self.checkin_checklist_id:
            self.checkin_checklist_id = self.create_checklist('checkin')
        else:
            checklist = self.checkin_checklist_id
            checklist_assets = checklist.line_ids.mapped('asset_id').ids
            extra_assets = self.assigned_assets_in_room.filtered(lambda a: a.id not in checklist_assets)
            if extra_assets:
                self.update_checklist(checklist, extra_assets)

        return {
            'name': 'Room Asset Check-In Checklist',
            'type': 'ir.actions.act_window',
            'res_model': 'camp.asset.checklist',
            'view_mode': 'form',
            'res_id': self.checkin_checklist_id.id,
            'target': 'current',
        }

    def action_open_checkout_checklist(self):
        """
        Opens the check-out checklist for review. Creates or updates it as needed
        and prepares it for final asset return verification.
        """
        self.ensure_one()
        if not self.checkout_checklist_id:
            self.checkout_checklist_id = self.create_checklist('checkout')
        else:
            checklist = self.checkout_checklist_id
            checklist_assets = checklist.line_ids.mapped('asset_id').ids
            extra_assets = self.assigned_assets_in_room.filtered(lambda a: a.id not in checklist_assets)
            if extra_assets:
                self.update_checklist(checklist, extra_assets)

        return {
            'name': 'Room Asset Check-Out Checklist',
            'type': 'ir.actions.act_window',
            'res_model': 'camp.asset.checklist',
            'view_mode': 'form',
            'res_id': self.checkout_checklist_id.id,
            'target': 'current',
        }

    @api.constrains('employee_id', 'external_employee_id')
    def _check_allocation_target(self):
        for rec in self:
            if not rec.employee_id and not rec.external_employee_id:
                raise ValidationError("You must allocate the asset to either an Employee or a Guest.")
            if rec.employee_id and rec.external_employee_id:
                raise ValidationError(
                    "You cannot allocate an asset to both an Employee and a Guest at the same time.")

    @api.onchange('allocation_type')
    def _onchange_allocation_type(self):
        for rec in self:
            if rec.allocation_type == 'internal':
                rec.external_contact_id = False
                rec.external_employee_id = False
            elif rec.allocation_type == 'external':
                rec.employee_id = False
                rec.project_id = False
                rec.company_id = False


class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    total_asset_count = fields.Integer(
        string="Total Assets",
        compute='_compute_global_asset_stats',
        store=False
    )
    allocated_asset_count = fields.Integer(
        string="Allocated Assets",
        compute='_compute_global_asset_stats',
        store=False
    )
    unallocated_asset_count = fields.Integer(
        string="Unallocated Assets",
        compute='_compute_global_asset_stats',
        store=False
    )
    total_room_count = fields.Integer(
        compute='_compute_global_camp_room_stats', store=False, string="Total Rooms")
    occupied_room_count = fields.Integer(
        compute='_compute_global_camp_room_stats', store=False, string="Occupied Rooms")
    vacant_room_count = fields.Integer(
        compute='_compute_global_camp_room_stats', store=False, string="Vacant Rooms")

    scrapped_asset_count = fields.Integer(string="Scrapped Assets", compute="_compute_scrapped_assets")
    it_asset_allocation_count = fields.Integer(string="IT Asset Allocated", compute="_compute_it_asset_allocations")
    tools_allocation_count = fields.Integer(string="IT Asset Allocated", compute="_compute_tools_equip_count")
    card_type = fields.Selection([
        ('asset', 'Asset Statistics'),
        ('camp', 'Camp Room Statistics'),
        ('it', 'IT Asset Allocation'),
        ('scrap', 'Scrapped Assets'),
        ('tools', 'Tools/Equipment'),
    ], string="Card Type", required=True)

    def _compute_it_asset_allocations(self):
        for rec in self:
            rec.it_asset_allocation_count = self.env['it.asset.allocation'].search_count([
            ])

    def _compute_scrapped_assets(self):
        for team in self:
            team.scrapped_asset_count = self.env['maintenance.equipment'].search_count([
                ('asset_lifecycle_status', '=', 'scrap')
            ])

    def _compute_tools_equip_count(self):
        for team in self:
            team.tools_allocation_count = self.env['tools.equipment.allocation'].search_count([
            ])

    @api.depends()
    def _compute_global_camp_room_stats(self):
        Room = self.env['camp.room']
        total = Room.search_count([])
        occupied = Room.search_count([('current_occupant_id', '!=', False)])
        for team in self:
            team.total_room_count = total
            team.occupied_room_count = occupied
            team.vacant_room_count = total - occupied

    @api.depends()
    def _compute_global_asset_stats(self):
        Equipment = self.env['maintenance.equipment']
        total_assets = Equipment.search([])
        allocated_assets = total_assets.filtered(lambda e: e.employee_id)

        total_count = len(total_assets)
        allocated_count = len(allocated_assets)
        unallocated_count = total_count - allocated_count

        for team in self:
            team.total_asset_count = total_count
            team.allocated_asset_count = allocated_count
            team.unallocated_asset_count = unallocated_count
