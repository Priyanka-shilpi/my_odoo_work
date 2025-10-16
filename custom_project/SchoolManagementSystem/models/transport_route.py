from odoo import models,fields,api


class TransportRoute(models.Model):
    _name = "transport.route"
    _description = "Transport Route"

    name = fields.Char(string="Route Name", compute="_compute_name", store=True)
    start_point = fields.Char(string="Starting Point") #, required=True
    end_point = fields.Char(string="End Point") #, required=True
    stop_names = fields.Text(string="Stops (comma-separated)")
    stops_list = fields.Char(compute='_compute_stops_list', string="Stop List", store=True)


    @api.depends('start_point', 'end_point')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.start_point} → {rec.end_point}"


    @api.depends('stop_names')
    def _compute_stops_list(self):
        for rec in self:
            if rec.stop_names:
                stops = [s.strip() for s in rec.stop_names.split(',') if s.strip()]
                rec.stops_list = ', '.join(stops)
            else:
                rec.stops_list = ""


