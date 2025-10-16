from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DriverAssignment(models.Model):
    _name = 'driver.assignment'
    _description = 'Driver Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'driver_id'

    driver_id = fields.Many2one(
        'hr.employee',
        string="Driver",
        required=True,
        tracking=True,
        domain=lambda self: self._get_available_driver_domain()
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Vehicle",
        required=True,
        tracking=True,
        domain=lambda self: self._get_available_vehicle_domain()
    )
    assignment_time = fields.Datetime(
        string="Assignment Time",
        default=fields.Datetime.now,
        readonly=True
    )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'On Duty'),
        ('completed', 'Available'),
    ], string="Status", default='draft', tracking=True, readonly=True)

    project_id = fields.Many2one('project.project', string="Project", required=True)
    license_type = fields.Selection([
        ('light', 'Light Vehicle'),
        ('heavy', 'Heavy Vehicle'),
    ], related='driver_id.license_type', string="License Type", store=True)
    required_license_type = fields.Selection([
        ('light', 'Light Vehicle'),
        ('heavy', 'Heavy Vehicle'),
    ], related='vehicle_id.required_license_type', string="License Type", store=True)
    assignment_date = fields.Date(
        string="Assignment Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    assignment_start = fields.Datetime(
        string="Date From",
        required=True,
        default=lambda self: fields.Datetime.now(),
        tracking=True
    )

    assignment_end = fields.Datetime(
        string="Date To",
        required=True,
        default=lambda self: fields.Datetime.now(),
        tracking=True
    )

    def _get_available_driver_domain(self):
        assigned_driver_ids = self.env['driver.assignment'].search([
            ('status', '=', 'active'),
            ('id', '!=', self.id),
        ]).mapped('driver_id.id')
        return [
            ('is_driver', '=', True),
            ('allocation_status', '!=', 'vacation'),
            ('id', 'not in', assigned_driver_ids),
        ]

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id:
            self.license_type = self.driver_id.license_type
        else:
            self.license_type = False

    @api.constrains('driver_id', 'vehicle_id', 'assignment_start', 'assignment_end')
    def _check_conflicts(self):
        for rec in self:
            if not rec.assignment_start or not rec.assignment_end:
                continue

            message_lines = []
            service_conflicts = self.env['fleet.vehicle.log.services'].search([
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('state', '=', 'running'),
                ('in_timestamp', '<=', rec.assignment_end),
                ('out_timestamp', '>=', rec.assignment_start),
            ])
            if service_conflicts:
                message_lines.append("The vehicle is currently in **Service**:")
                for svc in service_conflicts:
                    message_lines.append(
                        f" • Service: **{svc.service_type_id.name or 'N/A'}** from {svc.in_timestamp.strftime('%Y-%m-%d')} to {svc.out_timestamp.strftime('%Y-%m-%d')}"
                    )

            overlapping_driver = self.search([
                ('id', '!=', rec.id),
                ('driver_id', '=', rec.driver_id.id),
                ('status', '=', 'active'),
                ('assignment_start', '<=', rec.assignment_end),
                ('assignment_end', '>=', rec.assignment_start),
            ])
            if overlapping_driver:
                message_lines.append("Driver is already assigned during this time:")
                for od in overlapping_driver:
                    message_lines.append(
                        f" • {od.driver_id.name} assigned from {od.assignment_start.strftime('%Y-%m-%d %H:%M')} to {od.assignment_end.strftime('%Y-%m-%d %H:%M')}"
                    )

            # Vehicle assignment conflict
            overlapping_vehicle = self.search([
                ('id', '!=', rec.id),
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('status', '=', 'active'),
                ('assignment_start', '<=', rec.assignment_end),
                ('assignment_end', '>=', rec.assignment_start),
            ])
            if overlapping_vehicle:
                message_lines.append("Vehicle is already assigned during this time:")
                for ov in overlapping_vehicle:
                    message_lines.append(
                        f" • {ov.vehicle_id.name} assigned from {ov.assignment_start.strftime('%Y-%m-%d %H:%M')} to {ov.assignment_end.strftime('%Y-%m-%d %H:%M')}"
                    )

            if message_lines:
                raise ValidationError("\n".join(message_lines))

    def _get_available_vehicle_domain(self):
        assigned_vehicle_ids = self.env['driver.assignment'].search([
            ('status', '=', 'active'),
            ('id', '!=', self.id),
        ]).mapped('vehicle_id.id')

        return [('id', 'not in', assigned_vehicle_ids)]

    def action_reset_to_draft(self):
        for rec in self:
            rec.status = 'draft'

    def action_mark_active(self):
        for rec in self:
            rec.status = 'active'
            partner = rec.driver_id.work_contact_id
            if partner and rec.vehicle_id:
                rec.vehicle_id.driver_id = partner.id
                rec.vehicle_id.project_id = self.project_id.id

    def action_mark_completed(self):
        for rec in self:
            rec.status = 'completed'
            rec.driver_id.allocation_status = 'standby'
            partner = rec.driver_id.work_contact_id
            if partner and rec.vehicle_id.driver_id == partner:
                rec.vehicle_id.driver_id = False

            rec.driver_id.project_id = False
            rec.vehicle_id.project_id = False

    @api.model
    def create(self, vals):
        driver = self.env['hr.employee'].browse(vals.get('driver_id'))
        if not driver.is_driver:
            raise ValidationError("Selected employee is not marked as a driver.")

        res = super().create(vals)

        project = res.project_id
        vehicle = res.vehicle_id
        partner = driver.work_contact_id

        today = fields.Date.today()
        if res.status == 'active' and partner and vehicle:
            if res.assignment_start.date() <= today <= res.assignment_end.date():
                vehicle.driver_id = partner.id
                driver.allocation_status = 'in_project'

        if project:
            driver.project_id = project.id
            vehicle.project_id = project.id
        if res.status == 'active':
            self.env['fleet.vehicle.assignation.log'].create({
                'vehicle_id': res.vehicle_id.id,
                'driver_id': res.driver_id.res.driver_id.work_contact_id.id,
                'date_start': res.assignment_start,
                'date_end': res.assignment_end,
                'assignment_start': res.assignment_start,
                'assignment_end': res.assignment_end,
                'driver_assignment_id': res.id,
                'project_id': res.project_id.id,
                'status': res.status,
            })

        return res

    def write(self, vals):
        res = super().write(vals)

        for rec in self:
            driver = rec.driver_id
            vehicle = rec.vehicle_id
            project = rec.project_id
            partner = driver.work_contact_id

            today = fields.Date.today()

            if vals.get('status') == 'completed':
                if vehicle and vehicle.driver_id == partner:
                    vehicle.driver_id = False
                driver.project_id = False
                vehicle.project_id = False
                driver.allocation_status = 'standby'

            if 'driver_id' in vals and rec.status == 'active' and partner:
                if rec.assignment_start.date() <= today <= rec.assignment_end.date():
                    vehicle.driver_id = partner.id
                    driver.allocation_status = 'in_project'

            if 'vehicle_id' in vals and rec.status == 'active' and partner:
                if rec.assignment_start.date() <= today <= rec.assignment_end.date():
                    rec.vehicle_id.driver_id = partner.id

            if 'project_id' in vals:
                driver.project_id = rec.project_id.id
                vehicle.project_id = rec.project_id.id

            if vals.get('status') == 'active':
                if rec.assignment_start.date() <= today <= rec.assignment_end.date():
                    driver.allocation_status = 'in_project'

        return res

class FleetVehicleAssignationLog(models.Model):
    _inherit = 'fleet.vehicle.assignation.log'

    driver_assignment_id = fields.Many2one('driver.assignment', string="Driver Assignment")
    assignment_start = fields.Datetime(string="Assignment Start")
    assignment_end = fields.Datetime(string="Assignment End")
    assignment_ref_id = fields.Many2one('driver.assignment', string="Assignment Ref")
    project_id = fields.Many2one('project.project', string="Project")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ], string="Status")


class Project(models.Model):
    _inherit = 'project.project'

    driver_assignment_count = fields.Integer(
        string="Driver Assignment Count",
        compute="_compute_driver_assignment_count"
    )
    fuel_entry_count = fields.Integer(compute='_compute_fuel_entry_count')
    trip_count = fields.Integer(string="Trip Count", compute="_compute_trip_count")


    def _compute_driver_assignment_count(self):
        for project in self:
            project.driver_assignment_count = self.env['driver.assignment'].search_count([
                ('project_id', '=', project.id)
            ])

    def _compute_fuel_entry_count(self):
        for project in self:
            project.fuel_entry_count = self.env['fuel.entry'].search_count([('project_id', '=', project.id)])

    def action_view_fuel_entries(self):
        return {
            'name': 'Fuel Entries',
            'type': 'ir.actions.act_window',
            'res_model': 'fuel.entry',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }


    def _compute_trip_count(self):
        for record in self:
            record.trip_count = self.env['trip.management'].search_count([('project_id', '=', record.id)])

    def action_view_trips(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trips',
            'view_mode': 'tree,form',
            'res_model': 'trip.management',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
