from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FuelEntry(models.Model):
    _name = 'fuel.entry'
    _description = 'Fuel Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('hr.employee', string='Driver', required=True)
    project_id = fields.Many2one('project.project', string="Project", required=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account'
    )
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
        ('lpg', 'LPG'),
        ('lng', 'LNG'),
        ('biodiesel', 'Biodiesel'),
        ('ethanol', 'Ethanol'),
        ('hydrogen', 'Hydrogen'),
        ('methanol', 'Methanol'),
    ], string='Fuel Type', required=True)

    quantity = fields.Float(string='Quantity (Liters)', required=True)
    source = fields.Selection([
        ('inhouse', 'Inhouse'),
        ('external', 'External')
    ], string='Source', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department', store=True)

    unit_price = fields.Float(string="Unit Price")
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    journal_id = fields.Many2one(
        'account.journal',
        string="Expense Journal",
        domain=[('type', '=', 'purchase')],
        default=lambda self: self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
    )
    default_cash_bank_account_id = fields.Many2one(
        'account.account',
        string="Default Fuel Payment Account",
        domain=[('deprecated', '=', False), ('internal_type', 'in', ['cash', 'bank'])],
    )

    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='State', default='draft', readonly=True)

    @api.depends('driver_id')
    def _compute_department(self):
        for record in self:
            record.department_id = record.driver_id.department_id

    @api.depends('quantity', 'unit_price')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.quantity * record.unit_price

    @api.constrains('driver_id', 'vehicle_id')
    def _check_driver_assignment(self):
        for record in self:
            if record.vehicle_id.driver_ids and record.driver_id.id not in record.vehicle_id.driver_ids.ids:
                raise ValidationError("Driver is not assigned to this vehicle.")

    @api.onchange('vehicle_id', 'driver_id')
    def _onchange_project(self):
        if self.vehicle_id and self.driver_id:
            assignment = self.env['driver.assignment'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('driver_id', '=', self.driver_id.id),
            ], limit=1)
            if assignment:
                self.project_id = assignment.project_id

    def action_post(self):
        for record in self:
            if record.move_id:
                raise ValidationError("This fuel entry is already posted.")
            if not record.journal_id or not record.unit_price:
                raise ValidationError("Please set Unit Price and Journal.")
            if not record.project_id:
                raise ValidationError("Please select a Project before posting.")

            fuel_expense_account = self.env['account.account'].search([
                ('name', 'ilike', 'Fuel Expenses'),
                ('deprecated', '=', False)
            ], limit=1)
            if not fuel_expense_account:
                raise ValidationError("Please configure an account named 'Fuel Expenses' in your Chart of Accounts.")

            fuel_payment_account = record.default_cash_bank_account_id or self.env['account.account'].search([
                ('code', '=', '101001'),
                ('deprecated', '=', False)
            ], limit=1)
            if not fuel_payment_account:
                raise ValidationError("No valid cash/bank account found for fuel payment.")

            move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': record.date,
                'journal_id': record.journal_id.id,
                'ref': f"Fuel - {record.vehicle_id.name}",
                'line_ids': [
                    (0, 0, {
                        'name': f'Fuel for {record.vehicle_id.name}',
                        'account_id': fuel_expense_account.id,
                        'debit': record.total_cost,
                        'credit': 0.00,
                        'currency_id': record.currency_id.id,
                        'analytic_distribution': {record.project_id.analytic_account_id.id: 100.0}
                    }),
                    (0, 0, {
                        'name': 'Fuel Payment',
                        'account_id': fuel_payment_account.id,
                        'credit': record.total_cost,
                        'debit': 0.00,
                        'currency_id': record.currency_id.id,
                    }),
                ]
            })
            move.action_post()
            record.move_id = move.id
            record.state = 'posted'

    def reset_to_draft(self):
        for record in self:
            record.state = 'draft'

    def action_view_journal_entry(self):
        self.ensure_one()
        if not self.move_id:
            return
        return {
            'name': 'Journal Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        check_company=True,
    )

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    driver_ids = fields.Many2many('hr.employee', string='Assigned Drivers')
