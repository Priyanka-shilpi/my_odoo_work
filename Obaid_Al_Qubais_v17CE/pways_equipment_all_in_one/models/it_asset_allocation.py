from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ITAssetAllocation(models.Model):
    _name = 'it.asset.allocation'
    _description = 'IT Asset Allocation'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: ('New'))
    employee_id = fields.Many2one('hr.employee', string='Assigned To', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=False)
    allocation_date = fields.Date(string='Allocation Date', default=fields.Date.today, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('allocated', 'Allocated'),
        ('returned', 'Returned'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    employee_barcode = fields.Char(
        string="Employee ID",
        related='employee_id.barcode',
        store=True,
        readonly=True
    )
    checkin_checklist_id = fields.Many2one(
        'it.asset.checklist',
        string='Check-In Checklist',
        readonly=True
    )
    checkout_checklist_id = fields.Many2one(
        'it.asset.checklist',
        string='Check-Out Checklist',
        readonly=True
    )
    line_ids = fields.One2many(comodel_name='it.asset.allocation.line', inverse_name='allocation_id', string='IT Allocation Lines')

    # _sql_constraints = [
    #     ('unique_employee_barcode', 'unique(employee_barcode)', 'The employee barcode must be unique!')
    # ]

    def create_checklist(self, checklist_type):
        checklist = self.env['it.asset.checklist'].create({
            'employee_id': self.employee_id.id,
            'allocation_id': self.id,
            'checklist_type': checklist_type,
        })
        for line in self.line_ids:
            self.env['it.asset.checklist.line'].create({
                'checklist_id': checklist.id,
                'asset_id': line.asset_id.id,
                'serial_number': line.serial_number or '',
                'cost': line.cost or 0.0,
                'status': 'ok',
            })
        return checklist

    def update_checklist(self, checklist, extra_lines):
        for line in extra_lines:
            self.env['it.asset.checklist.line'].create({
                'checklist_id': checklist.id,
                'asset_id': line.asset_id.id,
                'serial_number': line.serial_number or '',
                'cost': line.cost or 0.0,
                'status': 'ok',
            })

    def action_open_checkin_checklist(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError("Add the Assets before allocating it.")

        assets = self.line_ids.mapped('asset_id')
        for asset in assets:
            if asset.state != 'validated':
                raise ValidationError(f"Asset-{asset.name} is not Validated Assets.\nOnly Validated Assets can be allocated.")
            if asset.employee_id:
                raise ValidationError(f"Asset-{asset.name} is already allocated to {asset.employee_id.name}")

        if not self.checkin_checklist_id:
            checklist = self.create_checklist('allocation')
            self.checkin_checklist_id = checklist
        else:
            checklist = self.checkin_checklist_id
            checklist_assets = checklist.line_ids.mapped('asset_id')
            extra_lines = self.line_ids.filtered(
                lambda l: l.asset_id.id not in checklist_assets.ids
            )
            if extra_lines:
                self.update_checklist(checklist, extra_lines)

        return {
            'name': 'Check-In Checklist',
            'type': 'ir.actions.act_window',
            'res_model': 'it.asset.checklist',
            'view_mode': 'form',
            'res_id': checklist.id,
            'target': 'current',
        }

    def action_open_checkout_checklist(self):
        self.ensure_one()
        if not self.checkout_checklist_id:
            checklist = self.create_checklist('return')
            self.checkout_checklist_id = checklist
        else:
            checklist = self.checkout_checklist_id
            checklist_assets = checklist.line_ids.mapped('asset_id')
            extra_lines = self.line_ids.filtered(
                lambda l: l.asset_id.id not in checklist_assets.ids
            )
            if extra_lines:
                self.update_checklist(checklist, extra_lines)

        return {
            'name': 'Check-Out Checklist',
            'type': 'ir.actions.act_window',
            'res_model': 'it.asset.checklist',
            'view_mode': 'form',
            'res_id': checklist.id,
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('it.asset.allocation') or 'New'
        return super().create(vals)

    def action_allocate(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Add the Assets before allocating it.")

            assets = rec.line_ids.mapped('asset_id')
            for asset in assets:
                if asset.state != 'validated':
                    raise ValidationError(
                        f"Asset-{asset.name} is not Validated Assets.\nOnly Validated Assets can be allocated.")
                if asset.employee_id:
                    raise ValidationError(f"Asset-{asset.name} is already allocated to {asset.employee_id.name}")

            checklist = rec.checkin_checklist_id
            if not checklist:
                raise ValidationError("Please check and verify the Check-In Checklist")

            if checklist.status == 'pending':
                raise ValidationError("Please verify the Checklist.\nOnly Verified checklist assets can be Allocated.")

            checklist_assets = checklist.line_ids.mapped('asset_id.id')
            allocation_assets = rec.line_ids.mapped('asset_id.id')
            checklist_assets.sort()
            allocation_assets.sort()
            if checklist_assets != allocation_assets:
                raise ValidationError("Allocation Assets and Checklist Assets are not matching")

            if rec.employee_id:
                for line in rec.line_ids:
                    line.asset_id.write({'employee_id': rec.employee_id.id})
            if rec.project_id:
                for line in rec.line_ids:
                    line.asset_id.write({'project_id': rec.project_id.id})

            rec.state = 'allocated'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_cancelled(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_return(self):
        for rec in self:
            checklist = rec.checkout_checklist_id
            if not checklist:
                raise ValidationError("Please check and verify the Check-Out Checklist")

            if checklist.status == 'pending':
                raise ValidationError("Please verify the Checklist.\nOnly Verified checklist assets can be Returned.")

            if rec.employee_id:
                for line in rec.line_ids:
                    line.asset_id.write({'employee_id': False})
            if rec.project_id:
                for line in rec.line_ids:
                    line.asset_id.write({'project_id': False})
            rec.state = 'returned'

    def notify_user(self):
        for rec in self:
            rec.message_post(
                body=f"@{rec.user_id.name} Please check this record.",
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )


class ITAssetAllocationLine(models.Model):
    _name = 'it.asset.allocation.line'
    _description = 'IT Asset Allocation Line'

    allocation_id = fields.Many2one(comodel_name='it.asset.allocation', string='IT Allocation')
    asset_id = fields.Many2one('maintenance.equipment', string='IT Equipment', required=True,
                               domain="[('employee_id', '=', False), ('project_id', '=', False), ('room_id', '=', False), ('state', '=', 'validated'), ('category_id.is_it_asset', '=', True)]")
    asset_tag_id = fields.Many2one('asset.tag.master', related='asset_id.asset_tag_id', store=True, string='Asset Tag')
    serial_number = fields.Char(string='Serial Number', related='asset_id.seq_number', readonly=True)
    cost = fields.Float("Cost", related='asset_id.product_cost')


class ToolsEquipmentAllocation(models.Model):
    _name = 'tools.equipment.allocation'
    _description = 'Tools/Equipment Allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True, required=True)
    employee_barcode = fields.Char(related='employee_id.barcode', string="Employee ID", readonly=True)
    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    allocation_date = fields.Date(string="Allocation Date", default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('allocated', 'Allocated'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', tracking=True)
    is_expensive = fields.Boolean(string="Expensive", compute="_compute_is_expensive")
    checkout_checklist_id = fields.Many2one('tools.asset.checklist', string='Check-Out Checklist', readonly=True)
    checkin_checklist_id = fields.Many2one('tools.asset.checklist', string='Check-In Checklist', readonly=True)
    line_ids = fields.One2many(comodel_name='tools.equipment.allocation.line', inverse_name='allocation_id', string='Allocation Lines')

    def create_checklist(self, checklist_type):
        checklist = self.env['tools.asset.checklist'].create({
            'employee_id': self.employee_id.id,
            'project_id': self.project_id.id,
            'allocation_id': self.id,
            'checklist_type': checklist_type,
        })
        for line in self.line_ids:
            self.env['tools.asset.checklist.line'].create({
                'checklist_id': checklist.id,
                'asset_id': line.asset_id.id,
                'serial_number': line.serial_number or '',
                'cost': line.cost or 0.0,
                'status': 'ok',
            })
        return checklist

    def update_checklist(self, checklist, extra_lines):
        for line in extra_lines:
            self.env['tools.asset.checklist.line'].create({
                'checklist_id': checklist.id,
                'asset_id': line.asset_id.id,
                'serial_number': line.serial_number or '',
                'cost': line.cost or 0.0,
                'status': 'ok',
            })

    def action_open_checkin_checklist(self):
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError("Add the Assets before allocating it.")

        assets = self.line_ids.mapped('asset_id')
        for asset in assets:
            if asset.state != 'validated':
                raise ValidationError(f"Asset-{asset.name} is not Validated Assets.\nOnly Validated Assets can be allocated.")
            if asset.employee_id:
                raise ValidationError(f"Asset-{asset.name} is already allocated to {asset.employee_id.name}")

        if not self.checkin_checklist_id:
            checklist = self.create_checklist('allocation')
            self.checkin_checklist_id = checklist
        else:
            checklist = self.checkin_checklist_id
            checklist_assets = checklist.line_ids.mapped('asset_id')
            extra_lines = self.line_ids.filtered(
                lambda l: l.asset_id.id not in checklist_assets.ids
            )
            if extra_lines:
                self.update_checklist(checklist, extra_lines)

        return {
            'name': 'Check-In Checklist',
            'type': 'ir.actions.act_window',
            'res_model': 'tools.asset.checklist',
            'view_mode': 'form',
            'res_id': checklist.id,
            'target': 'current',
        }

    def action_open_checkout_checklist(self):
        self.ensure_one()
        if not self.checkout_checklist_id:
            checklist = self.create_checklist('return')
            self.checkout_checklist_id = checklist
        else:
            checklist = self.checkout_checklist_id
            checklist_assets = checklist.line_ids.mapped('asset_id')
            extra_lines = self.line_ids.filtered(
                lambda l: l.asset_id.id not in checklist_assets.ids
            )
            if extra_lines:
                self.update_checklist(checklist, extra_lines)

        return {
            'name': 'Check-Out Checklist',
            'type': 'ir.actions.act_window',
            'res_model': 'tools.asset.checklist',
            'view_mode': 'form',
            'res_id': checklist.id,
            'target': 'current',
        }

    @api.onchange('line_ids')
    def _compute_is_expensive(self):
        """
        Sets is_expensive to True if any asset in line_ids is marked as expensive.
        Otherwise, sets it to False.
        """
        for record in self:
            assets = record.line_ids.mapped('asset_id')
            record.is_expensive = any(asset.is_expensive for asset in assets)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tools.equipment.allocation') or 'New'
        return super().create(vals)

    def action_allocate(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Add the Assets before allocating it.")

            assets = rec.line_ids.mapped('asset_id')
            for asset in assets:
                if asset.state != 'validated':
                    raise ValidationError(
                        f"Asset-{asset.name} is not Validated Assets.\nOnly Validated Assets can be allocated.")
                if asset.employee_id:
                    raise ValidationError(f"Asset-{asset.name} is already allocated to {asset.employee_id.name}")

            checklist = rec.checkin_checklist_id
            if not checklist:
                raise ValidationError("Please check and verify the Check-In Checklist")

            if checklist.status == 'pending':
                raise ValidationError("Please verify the Checklist.\nOnly Verified checklist assets can be Allocated.")

            checklist_assets = checklist.line_ids.mapped('asset_id.id')
            allocation_assets = rec.line_ids.mapped('asset_id.id')
            checklist_assets.sort()
            allocation_assets.sort()
            if checklist_assets != allocation_assets:
                raise ValidationError("Allocation Assets and Checklist Assets are not matching")

            if rec.employee_id:
                for line in rec.line_ids:
                    line.asset_id.write({'employee_id': rec.employee_id.id})
            if rec.project_id:
                for line in rec.line_ids:
                    line.asset_id.write({'project_id': rec.project_id.id})

            rec.state = 'allocated'

    def action_return(self):
        for rec in self:
            checklist = rec.checkout_checklist_id
            if not checklist:
                raise ValidationError("Please check and verify the Check-Out Checklist")

            if checklist.status == 'pending':
                raise ValidationError("Please verify the Checklist.\nOnly Verified checklist assets can be Returned.")

            if rec.employee_id:
                for line in rec.line_ids:
                    line.asset_id.write({'employee_id': False})
            if rec.project_id:
                for line in rec.line_ids:
                    line.asset_id.write({'project_id': False})
            rec.state = 'returned'

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_cancelled(self):
        self.write({'state': 'cancelled'})


class ToolsEquipmentAllocationLine(models.Model):
    _name = 'tools.equipment.allocation.line'
    _description = 'Tools/Equipment Allocation Line'

    allocation_id = fields.Many2one(comodel_name='tools.equipment.allocation', string='Allocation')
    asset_id = fields.Many2one('maintenance.equipment', string="Tool/Equipment", required=True,
                               domain="[('employee_id', '=', False), ('project_id', '=', False), ('room_id', '=', False), ('state', '=', 'validated'), ('category_id.is_equipment_asset', '=', True)]")
    asset_tag_id = fields.Many2one('asset.tag.master', related='asset_id.asset_tag_id', store=True, string='Asset Tag')
    serial_number = fields.Char(related='asset_id.seq_number', string="Serial Number", readonly=True)
    cost = fields.Float(string="Estimated Value", related='asset_id.product_cost', tracking=True)