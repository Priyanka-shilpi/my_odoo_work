from datetime import date
import io
import base64
import xlsxwriter
from odoo import models, fields, api
from odoo.exceptions import UserError


class TripTicket(models.Model):
    _name = 'trip.ticket'
    _description = 'Trip Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Ticket Number', required=True, default='/')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('hr.employee', string='Driver', required=True)
    date = fields.Date(string='Trip Date', default=fields.Date.context_today)
    route = fields.Char(string='Route')
    type_of_work = fields.Char(string='Route')
    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    odometer_start = fields.Float(string='Odometer Start (km)')
    odometer_end = fields.Float(string='Odometer End (km)')
    fuel_used = fields.Float(string='Fuel Used (litres)')
    remarks = fields.Text(string='Remarks')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Completed')
    ], default='draft', string='Status')
    charge_amount = fields.Monetary(string="Charge", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    invoice_id = fields.Many2one('account.move', string="Invoice")
    customer_id = fields.Many2one('res.partner', string="Customer")
    amount = fields.Float(string="Charge Amount")
    is_invoiced = fields.Boolean(string='Invoiced', default=False)
    distance = fields.Float(string="Distance Travelled (km)", compute='_compute_distance', store=True)


    @api.constrains('vehicle_id', 'start_time', 'end_time')
    def _check_vehicle_availability(self):
        for rec in self:
            if not rec.vehicle_id or not rec.start_time or not rec.end_time:
                continue

            message_lines = []

            service_conflicts = self.env['fleet.vehicle.log.services'].search([
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('state', '=', 'running'),
                ('in_timestamp', '<=', rec.end_time),
                ('out_timestamp', '>=', rec.start_time),
            ])
            if service_conflicts:
                message_lines.append("The vehicle is in Service")
                for svc in service_conflicts:
                    message_lines.append(f" • Service: **{svc.service_type_id.name or 'N/A'}** on {svc.in_timestamp.strftime('%Y-%m-%d')} to {svc.out_timestamp.strftime('%Y-%m-%d')} ")

            trip_conflicts = self.env['trip.management'].search([
                ('plate_id', '=', rec.vehicle_id.id),
                ('start_datetime', '<=', rec.end_time),
                ('end_datetime', '>=', rec.start_time),
            ])
            if trip_conflicts:
                message_lines.append("The vehicle is already in another Trip")
                for trip in trip_conflicts:
                    message_lines.append(
                        f" • Reference: **{trip.reference or 'N/A'}** from {trip.start_datetime.strftime('%Y-%m-%d %H:%M')} to {trip.end_datetime.strftime('%Y-%m-%d %H:%M')}"
                    )

            ticket_conflicts = self.env['trip.ticket'].search([
                ('id', '!=', rec.id),
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('start_time', '<=', rec.end_time),
                ('end_time', '>=', rec.start_time),
            ])
            if ticket_conflicts:
                message_lines.append("The vehicle is already scheduled in another Trip Ticket")
                for ticket in ticket_conflicts:
                    message_lines.append(
                        f" • Ticket: **{ticket.name or 'N/A'}** from {ticket.start_time.strftime('%Y-%m-%d %H:%M')} to {ticket.end_time.strftime('%Y-%m-%d %H:%M')}"
                    )

            if message_lines:
                raise UserError("\n".join(message_lines))

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id and self.vehicle_id.driver_id:
            partner = self.vehicle_id.driver_id
            employee = self.env['hr.employee'].search([
                '|',
                ('user_id.partner_id', '=', partner.id),
                ('work_contact_id', '=', partner.id)
            ], limit=1)
            if employee:
                self.driver_id = employee
            else:
                self.driver_id = False
        else:
            self.driver_id = False

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('trip.ticket') or '/'

        ticket = super().create(vals)

        if ticket.driver_id and ticket.vehicle_id and ticket.start_time and ticket.end_time:
            assignment = self.env['driver.assignment'].search([
                ('driver_id', '=', ticket.driver_id.id),
                ('vehicle_id', '=', ticket.vehicle_id.id),
            ], limit=1)

            if assignment:
                assignment.assignment_start = ticket.start_time
                assignment.assignment_end = ticket.end_time

            overlapping_assignments = self.env['driver.assignment'].search([
                ('vehicle_id', '=', ticket.vehicle_id.id),
                ('assignment_start', '<=', ticket.end_time),
                ('assignment_end', '>=', ticket.start_time),
            ])

            if overlapping_assignments:
                msg_lines = ["⚠️ This vehicle is already assigned during the selected time:"]
                for assign in overlapping_assignments:
                    msg_lines.append(
                        f" • Driver: {assign.driver_id.name}, "
                        f"{assign.assignment_start.strftime('%Y-%m-%d %H:%M')} to {assign.assignment_end.strftime('%Y-%m-%d %H:%M')}"
                    )

                ticket.message_post(body="<br/>".join(msg_lines))

        return ticket

    @api.depends('odometer_start', 'odometer_end')
    def _compute_distance(self):
        for rec in self:
            rec.distance = rec.odometer_end - rec.odometer_start if rec.odometer_end and rec.odometer_start else 0.0



    def print_trip_ticket(self):
        return self.env.ref('sdm_trip_management.action_report_trip_ticket').report_action(self)

    def action_generate_invoice(self):
        for ticket in self:
            if ticket.invoice_id:
                continue

            income_account = self.env['account.account'].search([
                ('account_type', '=', 'income')
            ], limit=1)
            if not income_account:
                raise UserError("No income account found for this company.")

            move = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': ticket.driver_id.id or self.env.user.partner_id.id,
                'invoice_origin': ticket.name,
                'invoice_date': fields.Date.today(),
                'currency_id': ticket.currency_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': f'Trip: {ticket.name} - {ticket.route or ""}',
                    'quantity': 1,
                    'price_unit': ticket.charge_amount or 0.0,
                    'account_id': income_account.id,
                })],
            })

            ticket.invoice_id = move.id
            ticket.is_invoiced = True

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': ticket.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    def action_done(self):
        self.state = 'done'

    # def open_invoice(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Invoice',
    #         'view_mode': 'form',
    #         'res_model': 'account.move',
    #         'res_id': self.invoice_id.id,
    #         'target': 'current',
    #     }


class TripTicketReport(models.Model):
    _name = 'trip.ticket.report'
    _description = 'Trip Ticket Summary Report'
    _auto = False

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    month = fields.Char(string='Month')
    trip_count = fields.Integer(string='Number of Trips')

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW trip_ticket_report AS (
                SELECT
                    MIN(id) as id,
                    vehicle_id,
                    TO_CHAR(date, 'YYYY-MM') as month,
                    COUNT(*) as trip_count
                FROM
                    trip_ticket
                GROUP BY vehicle_id, TO_CHAR(date, 'YYYY-MM')
            )
        """)

class TripTicketReportWizard(models.TransientModel):
    _name = 'trip.ticket.report.wizard'
    _description = 'Trip Ticket Report Wizard'

    date_from = fields.Date(string="Start Date", required=True, default=date.today().replace(day=1))
    date_to = fields.Date(string="End Date", required=True, default=date.today())
    file_data = fields.Binary("Excel File", readonly=True)
    file_name = fields.Char("Filename", readonly=True)

    def action_generate_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Trip Tickets")

        headers = ['Ticket Number', 'Vehicle', 'Driver', 'Date', 'Route', 'Odometer Start', 'Odometer End', 'Fuel Used', 'Remarks']
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        tickets = self.env['trip.ticket'].search(domain)

        for row, ticket in enumerate(tickets, start=1):
            sheet.write(row, 0, ticket.name)
            sheet.write(row, 1, ticket.vehicle_id.name)
            sheet.write(row, 2, ticket.driver_id.name)
            sheet.write(row, 3, str(ticket.date))
            sheet.write(row, 4, ticket.route or '')
            sheet.write(row, 5, ticket.odometer_start)
            sheet.write(row, 6, ticket.odometer_end)
            sheet.write(row, 7, ticket.fuel_used)
            sheet.write(row, 8, ticket.remarks or '')

        workbook.close()
        output.seek(0)
        self.file_data = base64.b64encode(output.read())
        self.file_name = f"Trip_Tickets_{self.date_from}_to_{self.date_to}.xlsx"

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'trip.ticket.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }







