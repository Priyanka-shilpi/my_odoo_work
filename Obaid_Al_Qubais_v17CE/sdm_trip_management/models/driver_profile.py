from odoo import models, fields,api
from datetime import date


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_driver = fields.Boolean(string="Is Driver")
    is_mechanic = fields.Boolean(string="Is Mechanic")
    license_type = fields.Selection([
        ('light', 'Light Vehicle'),
        ('heavy', 'Heavy Vehicle'),
    ], string="License Type")
    license_number = fields.Char(string="License No.")
    license_expiry_date = fields.Date(string="License Expiry Date")
    allocation_status = fields.Selection([
        ('in_project', 'In Project'),
        ('standby', 'Standby'),
        ('vacation', 'Vacation')
    ], string="Allocation Status", default='standby')
    license_expired = fields.Boolean(string="License Expired", compute="_compute_license_expired", store=True)

    vehicle_id = fields.Many2one('fleet.vehicle', string="Linked Vehicle")
    project_id = fields.Many2one('project.project', string="Project")

    @api.depends('license_expiry_date')
    def _compute_license_expired(self):
        today = date.today()
        for rec in self:
            rec.license_expired = rec.license_expiry_date and rec.license_expiry_date < today
