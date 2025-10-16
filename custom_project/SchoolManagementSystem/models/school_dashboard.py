
from odoo import models, fields, api

class SchoolDashboard(models.Model):
    _name = 'school.dashboard'
    _description = 'School Dashboard'

    GROUP_SELECTION = [
        ('student', 'Students'),
        ('teacher', 'Teachers'),
        ('parent', 'Parents'),
        ('driver', 'Drivers'),
    ]

    name = fields.Char(string='Group Name', readonly=True)
    group_type = fields.Selection(GROUP_SELECTION, required=True, readonly=True)
    count = fields.Integer(string='Count', compute="_compute_count", store=True)

    student_count = fields.Integer("Total Students", compute="_compute_counts", store=True)
    teacher_count = fields.Integer("Total Teachers", compute="_compute_counts", store=True)
    parent_count = fields.Integer("Total Parents", compute="_compute_counts", store=True)
    driver_count = fields.Integer("Total Drivers", compute="_compute_counts", store=True)
    chart_data = fields.Json(string="Chart Data")
    @api.depends('group_type')
    def _compute_count(self):
        for record in self:
            if record.group_type == 'student':
                record.count = self.env['school.student'].search_count([])
            elif record.group_type == 'teacher':
                record.count = self.env['hr.employee'].search_count([])  # FIXED!
            elif record.group_type == 'parent':
                record.count = self.env['users.parents'].search_count([])
            elif record.group_type == 'driver':
                record.count = self.env['school.drivers'].search_count([])

    @api.depends()
    def _compute_counts(self):
        for record in self:
            record.student_count = self.env['school.student'].search_count([])
            record.teacher_count = self.env['hr.employee'].search_count([])
            record.parent_count = self.env['users.parents'].search_count([])
            record.driver_count = self.env['school.drivers'].search_count([])