from odoo import models, fields, api
from datetime import timedelta
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    driver_id = fields.Many2one('res.partner', string='Driver', tracking=True)
    required_license_type = fields.Selection([
        ('light', 'Light Vehicle'),
        ('heavy', 'Heavy Vehicle'),
    ])
    insurance_expiration_date = fields.Date(string="Insurance Expiry Date")
    license_expiration_date = fields.Date(string="License Expiry Date")
    assignment_count = fields.Integer(string="Assignment Count", compute="_compute_assignment_count")
    plan_to_change_car = fields.Boolean(string="Plan to Change Car")
    certification = fields.Char(string="Certification")
    reference_number = fields.Char(string="Reference Number")
    cicpa_expiry_date = fields.Date(string="CICPA Expiry Date")
    cicpa_location = fields.Char(string="CICPA Location")
    cicpa_document_1 = fields.Binary(string="CICPA Document 1")
    cicpa_document_2 = fields.Binary(string="CICPA Document 2")
    cicpa_document_3 = fields.Binary(string="CICPA Document 3")
    cicpa_document_4 = fields.Binary(string="CICPA Document 4")
    driver_ids = fields.Many2many('hr.employee', string='Assigned Drivers')
    project_id = fields.Many2one('project.project', string="Assigned Project")
    registration_certificate_expiry = fields.Date(string="Registration Certificate(Mulkiya) Expiry")
    ivms_certificate = fields.Boolean(string="IVMS Certificate Available")
    license_expiry_date = fields.Date(string="Licence Expiry Date")
    registration_certificate_start = fields.Date(string="Registration Certificate Start Date")
    trip_ids = fields.One2many('trip.management', 'plate_id', string="Trips")
    trip_count = fields.Integer(string="Trip Count", compute="_compute_trip_count")
    employee_driver_id = fields.Many2one(
        'hr.employee',
        string='Employee Driver',
        compute='_compute_employee_driver_id',
        store=False
    )

    @api.depends('driver_id')
    def _compute_employee_driver_id(self):
        for rec in self:
            employee = self.env['hr.employee'].search([
                '|',
                ('user_id.partner_id', '=', rec.driver_id.id),
                ('work_contact_id', '=', rec.driver_id.id)
            ], limit=1)
            rec.employee_driver_id = employee if employee else False

    @api.depends('trip_ids')
    def _compute_trip_count(self):
        for vehicle in self:
            vehicle.trip_count = len(vehicle.trip_ids)

    def _compute_assignment_count(self):
        for vehicle in self:
            vehicle.assignment_count = self.env['driver.assignment'].search_count([('vehicle_id', '=', vehicle.id)])


    @api.model
    def check_expiry_alerts(self):
        today = fields.Date.today()
        alert_days = [30, 15, 7]
        for days in alert_days:
            exp_date = today + timedelta(days=days)
            expiring_vehicles = self.search([
                '|',
                ('insurance_expiration_date', '=', exp_date),
                ('license_expiration_date', '=', exp_date),
            ])
            for vehicle in expiring_vehicles:
                vehicle._send_expiry_notification(days)

    def _send_expiry_notification(self, days):
        template = self.env.ref('sdm_trip_management.email_template_vehicle_expiry_alert', raise_if_not_found=False)
        if template:
            template.with_context(force_send=True).send_mail(self.id, force_send=True)

    def post_monthly_trip_costs(self):
        today = fields.Date.today()
        for vehicle in self.search([('monthly_cost', '>', 0)]):
            if not vehicle.last_cost_post_date or vehicle.last_cost_post_date.month != today.month:
                move = self.env['account.move'].create({
                    'move_type': 'entry',
                    'date': today,
                    'journal_id': self.env['account.journal'].search([('type', '=', 'purchase')], limit=1).id,
                    'ref': f"Monthly cost for {vehicle.name} - {today.strftime('%B')}",
                    'line_ids': [
                        (0, 0, {
                            'name': f'Internal Vehicle Cost - {vehicle.name}',
                            'account_id': self.env['account.account'].search([('account_type', '=', 'expense')],
                                                                             limit=1).id,
                            'debit': vehicle.monthly_cost,
                        }),
                        (0, 0, {
                            'name': 'Vehicle Cost Credit',
                            'account_id': self.env['account.account'].search([('account_type', '=', 'payable')],
                                                                             limit=1).id,
                            'credit': vehicle.monthly_cost,
                        }),
                    ]
                })
                move.action_post()
                vehicle.last_cost_post_date = today

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    in_timestamp = fields.Datetime(string="IN Timestamp")
    out_timestamp = fields.Datetime(string="OUT Timestamp")
    wrench_time = fields.Float(string="Wrench Time (Hours)", compute="_compute_wrench_time", store=True)
    hide_mark_button = fields.Boolean(compute="_compute_hide_button", store=False)

    service_status = fields.Selection([
        ('in_service', 'In Service'),
        ('external_repair', 'Out for External Repair'),
        ('completed', 'Completed')
    ], string="Service Status", default='in_service', tracking=True)

    consumable_line_ids = fields.One2many(
        'fleet.vehicle.service.part.line',
        'service_id',
        string="Consumables & Parts Used"
    )
    job_card_id = fields.Many2one('garage.job.card', string="Job Card")
    is_inhouse = fields.Boolean(string="In-House Service", default=True, readonly=True)
    sap_cost_fetched = fields.Boolean(string="Cost Fetched", default=False, readonly=True)
    sap_cost_total = fields.Float(string="Total Cost", readonly=True)
    accounting_entry_created = fields.Boolean(string="Accounting Entry Created", default=False, invisible=True)
    move_ids = fields.One2many(
        'account.move',
        'fleet_service_id',
        string="Vendor Bills",
        domain=[('move_type', '=', 'in_invoice')]
    )
    invoice_id = fields.Many2one('account.move', string='Vendor Bill')
    invoice_number = fields.Char(string='Invoice Number', compute='_compute_invoice_number', store=True)

    @api.depends('invoice_id')
    def _compute_invoice_number(self):
        for rec in self:
            rec.invoice_number = rec.invoice_id.name if rec.invoice_id else ''

    @api.depends('service_status')
    def _compute_hide_button(self):
        for rec in self:
            rec.hide_mark_button = rec.service_status == 'completed'


    def action_mark_completed(self):
        for record in self:
            record.service_status = 'completed'
            record.state = 'done'
            if record.job_card_id:
                record.job_card_id.state = 'closed'
            if not record.out_timestamp:
                record.out_timestamp = fields.Datetime.now()

    @api.depends('in_timestamp', 'out_timestamp')
    def _compute_wrench_time(self):
        for rec in self:
            if rec.in_timestamp and rec.out_timestamp:
                delta = rec.out_timestamp - rec.in_timestamp
                rec.wrench_time = round(delta.total_seconds() / 3600.0, 2)
            else:
                rec.wrench_time = 0.0

    def action_create_accounting_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError("No purchase journal found.")

        for service in self:
            invoice = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': service.vendor_id.id,
                'journal_id': journal.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': f'Service for {service.job_card_id.id}',
                    'quantity': 1,
                    'price_unit': service.sap_cost_total,
                    'account_id': journal.default_account_id.id or self.env['account.account'].search(
                        [('internal_type', '=', 'expense')], limit=1).id
                })]
            })
            invoice.action_post()
            service.invoice_id = invoice
            service.accounting_entry_created = True


class AccountMove(models.Model):
    _inherit = 'account.move'

    fleet_service_id = fields.Many2one('fleet.vehicle.log.services', string="Related Fleet Service")



class FleetVehicleServicePartLine(models.Model):
    _name = 'fleet.vehicle.service.part.line'
    _description = 'Service Consumable / Spare Part Line'

    service_id = fields.Many2one('fleet.vehicle.log.services', string="Service Reference", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Item", required=True)
    quantity = fields.Float(string="Quantity", required=True)
    usage_type = fields.Selection([
        ('in', 'IN'),
        ('out', 'OUT')
    ], string="IN/OUT", default='out', required=True)
    usage_reason = fields.Text(string="Usage Reason")
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    used_date = fields.Date(string="Date", default=fields.Date.context_today)
    vehicle_id = fields.Many2one(related='service_id.vehicle_id', store=True, string="Vehicle")
