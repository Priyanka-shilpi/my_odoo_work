from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date


class FleetGatchSupplySheet(models.Model):
    _name = 'fleet.gatch.supply'
    _description = 'Gatch Supply Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Reference", required=True, default='New', copy=False)
    bill_to_id = fields.Many2one('res.partner', string="Bill To", required=True)
    trip_ticket_no = fields.Many2one('trip.ticket', string="Ticket No")
    license_plate = fields.Many2one('fleet.vehicle', string="License")
    driver_name = fields.Many2one('hr.employee', string="Driver")
    invoice_for = fields.Char(string="Invoice For", default="TRIP SERVICE")
    qty_m3 = fields.Integer(string="Qty")
    part_cost = fields.Float(string="Cost")
    location = fields.Char(string="Location")
    month = fields.Char(string="Month")
    invoice_no = fields.Many2one('account.move', string="Invoice", readonly=True)
    generate_invoice = fields.Many2one('account.move', string="Invoice", readonly=True)
    line_ids = fields.One2many('fleet.gatch.supply.line', 'sheet_id', string="Lines")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),('posted','Posted')], default='draft', tracking=True)
    date = fields.Date("date")
    service_type_id = fields.Many2one('gatch.service.type', string="Service Type")
    total_qty = fields.Float(string="Total Qty", compute="_compute_total_qty", store=True)
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    done_date = fields.Datetime(string="Date", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('fleet.gatch.supply') or 'New'
        return super().create(vals)

    @api.depends('line_ids.qty_m3')
    def _compute_total_qty(self):
        for rec in self:
            rec.total_qty = sum(line.qty_m3 for line in rec.line_ids)

    @api.depends('line_ids.total_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = sum(line.total_cost for line in rec.line_ids)
    def action_set_done(self):
        for rec in self:
            rec.state = 'done'
            rec.done_date = fields.Datetime.now()

    def action_create_invoice(self):
        for rec in self:
            if not rec.bill_to_id:
                raise UserError("Bill To (Customer) is required to generate the invoice.")

            if not rec.line_ids:
                raise UserError("Cannot generate invoice without lines.")

            invoice_lines = []
            for line in rec.line_ids:
                invoice_lines.append((0, 0, {
                    'name': line.description or "Gatch Supply",
                    'quantity': line.qty_m3,
                    'price_unit': line.part_cost,
                    'account_id': self.env['account.account'].search([('account_type', '=', 'income')], limit=1).id,
                }))

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': rec.bill_to_id.id,
                'invoice_date': fields.Date.context_today(self),
                'invoice_origin': rec.name,
                'invoice_line_ids': invoice_lines,
            })

            rec.invoice_no = invoice.id
            rec.state = 'posted'


class FleetGatchSupplyLine(models.Model):
    _name = 'fleet.gatch.supply.line'
    _description = 'Gatch Supply Line Entry'
    _order = 'date desc'

    sheet_id = fields.Many2one('fleet.gatch.supply', string="Sheet", ondelete="cascade")
    date = fields.Date(required=True)
    trip_ticket_no = fields.Many2one('trip.ticket', string="Ticket No")
    license_plate = fields.Many2one('fleet.vehicle', string="Plate No", required=True)
    driver_name = fields.Many2one('hr.employee', string="Driver")
    description = fields.Text(string="Description")
    qty_m3 = fields.Float(string="Qty", required=True)
    part_cost = fields.Float(string="Unit Cost")
    total_cost = fields.Float(string="Total Cost", compute="_compute_total_cost", store=True)

    @api.onchange('sheet_id')
    def _onchange_sheet_id(self):
        if self.sheet_id and self.sheet_id.service_type_id:
            self.description = self.sheet_id.service_type_id.name

    @api.depends('qty_m3', 'part_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.qty_m3 * rec.part_cost if rec.qty_m3 and rec.part_cost else 0.0


