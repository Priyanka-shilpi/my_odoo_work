from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class TripManagement(models.Model):
    _name = 'trip.management'
    _rec_name = 'reference'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reference = fields.Char(string="Reference Number", tracking=True, readonly=True, copy=False, default="New",
                            required=True)
    plate_id = fields.Many2one('fleet.vehicle', string="Vehicle Plate Number", tracking=True, required=True,domain=[('driver_id', '!=', False)])
    driver_id = fields.Many2one(
        'hr.employee',
        string="Driver",
        required=True,
        tracking=True,
        domain=lambda self: self._get_available_driver_domain()
    )
    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    trip_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Trip Type', tracking=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    location = fields.Char(string="Location")
    work_type = fields.Selection([
        ('sewage', 'Sewage'),
        ('water', 'Water'),
        ('construction', 'Construction'),
        ('other', 'Other'),
    ], string="Type of Work")
    quantity = fields.Float(string="Quantity")
    authorised_by = fields.Char(string="Authorised By")

    charge_ids = fields.One2many('daily.charge', 'trip_id', string='Trip Charges')
    invoice_id = fields.Many2one('account.move', string="Generated Invoice", readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
    ], default='draft', string="Status")
    start_location = fields.Char(string="Start location", required=True)
    destination = fields.Char(string="End location", required=True)
    # monthly_cost_id = fields.Many2one('vehicle.monthly.cost', string="Vehicle Monthly Cost")
    start_datetime = fields.Datetime(string="Start Time")
    end_datetime = fields.Datetime(string="End Time")

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

    @api.model
    def create(self, vals):
        if vals.get('reference', '/') == '/':
            vals['reference'] = self.env['ir.sequence'].next_by_code('trip.management') or '/'
        trip = super().create(vals)

        if trip.project_id:
            trip.plate_id.write({'project_id': trip.project_id.id})
            if hasattr(trip.driver_id, 'project_id'):
                trip.driver_id.write({'project_id': trip.project_id.id})

        if trip.driver_id:
            if hasattr(trip.driver_id, 'vehicle_id'):
                trip.driver_id.write({'vehicle_id': trip.plate_id.id})

            partner = trip.driver_id.work_contact_id
            if partner:
                trip.plate_id.write({'driver_id': partner.id})

        return trip

    def write(self, vals):
        res = super().write(vals)
        for trip in self:
            if 'project_id' in vals:
                if trip.plate_id:
                    trip.plate_id.project_id = trip.project_id.id
                if trip.driver_id:
                    trip.driver_id.project_id = trip.project_id.id
        return res


    def action_running(self):
        self.state = 'running'


    def action_completed(self):
        self.state = 'completed'

    def action_generate_invoice(self):
        for trip in self:
            if trip.invoice_id:
                raise ValidationError("Invoice already exists for this trip.")

            if not trip.charge_ids:
                raise ValidationError("No charges found for this trip.")

            move_type = 'out_invoice' if trip.trip_type == 'external' else 'in_invoice'
            lines = []
            for charge in trip.charge_ids:
                account = self.env['account.account'].search([
                    ('account_type', '=', 'expense')
                ], limit=1)
                if not account:
                    raise ValidationError("No expense account found. Please configure an account with type 'Expense'.")

                lines.append((0, 0, {
                    'name': f"{charge.cost_type.capitalize()} Charge",
                    'quantity': 1,
                    'price_unit': charge.amount,
                    'account_id': account.id,
                }))

            partner_id = self.env.user.partner_id.id

            invoice = self.env['account.move'].create({
                'move_type': move_type,
                'partner_id': partner_id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': lines,
                'ref': trip.reference,
            })

            trip.invoice_id = invoice.id

    @api.onchange('plate_id')
    def _onchange_plate_id(self):
        if self.plate_id:
            self.project_id = self.plate_id.project_id.id if self.plate_id.project_id else False
            partner = self.plate_id.driver_id
            if partner:
                employee = self.env['hr.employee'].search([
                    # '|',
                    # ('user_id.partner_id', '=', partner.id),
                    ('work_contact_id', '=', partner.id)
                ], limit=1)
                self.driver_id = employee if employee else False
            else:
                self.driver_id = False
        else:
            self.driver_id = False
            self.project_id = False

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            if self.plate_id:
                self.plate_id.project_id = self.project_id.id
            if self.driver_id:
                self.driver_id.project_id = self.project_id.id

    @api.constrains('plate_id', 'start_datetime', 'end_datetime')
    def _check_vehicle_availability(self):
        for record in self:
            if not record.plate_id or not record.start_datetime or not record.end_datetime:
                continue

            overlapping_trips = self.search([
                ('id', '!=', record.id),
                ('plate_id', '=', record.plate_id.id),
                ('start_datetime', '<=', record.end_datetime),
                ('end_datetime', '>=', record.start_datetime),
                ('state', 'in', ['running', 'draft']),
            ])

            service_conflicts = self.env['fleet.vehicle.log.services'].search([
                ('vehicle_id', '=', record.plate_id.id),
                ('state', '=', 'running'),
                ('in_timestamp', '<=', record.end_datetime),
                ('out_timestamp', '>=', record.start_datetime),
            ])

            message_lines = []

            if overlapping_trips:
                message_lines.append("The vehicle is already assigned to **another trip**:")
                for trip in overlapping_trips:
                    message_lines.append(
                        f" • Trip Ref: **{trip.reference}** from {trip.start_datetime.strftime('%Y-%m-%d %H:%M')} to {trip.end_datetime.strftime('%Y-%m-%d %H:%M')}"
                    )

            if service_conflicts:
                message_lines.append("The vehicle is currently in **Service**:")
                for svc in service_conflicts:
                    message_lines.append(
                        f" • Service: **{svc.service_type_id.name or 'N/A'}** from {svc.in_timestamp.strftime('%Y-%m-%d %H:%M')} to {svc.out_timestamp.strftime('%Y-%m-%d %H:%M')}"
                    )

            if message_lines:
                raise ValidationError("\n".join(message_lines))


class DriverList(models.Model):
    _name = 'driver.list'
    _rec_name = 'name'

    name = fields.Many2one('res.users', string='Select Driver')
