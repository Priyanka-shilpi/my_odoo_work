from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fleet_alert_email = fields.Char(
        string="Fleet Alert Email ID",
        config_parameter='fleet.fleet_alert_email',
        help="Email address where fleet expiry alerts will be sent."
    )
