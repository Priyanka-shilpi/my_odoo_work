from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    prjcode = fields.Char(string="Task Code")
    validfrom = fields.Date(string="Valid From")
    validto = fields.Date(string="Valid TO")
    pro_active = fields.Date(string="Valid TO")
    active = fields.Char(string="Active")

class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    custom_serial_number = fields.Char(string="Serial Number")
    warranty_expiration_date = fields.Date(string="Warranty Expiration Date")