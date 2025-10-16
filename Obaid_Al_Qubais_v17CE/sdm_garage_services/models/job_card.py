from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessError
_logger = logging.getLogger(__name__)


class GarageJobCard(models.Model):
    _name = 'garage.job.card'
    _description = 'Garage Job Card'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Job Card No.", required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string="Date", default=fields.Date.today)
    job_type_id = fields.Many2one('garage.job.type', string="Job Type")
    asset_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    last_service_km = fields.Float(string="Last Service KM/Hrs")
    current_km = fields.Float(string="KM")
    hours = fields.Float(string="Hours")
    checklist_ids = fields.One2many(
        'garage.job.card.checklist.line',
        'job_card_id',
        string="Checklist"
    )

    state = fields.Selection([
        ('new', 'New'),
        ('running', 'Running'),
        ('closed', 'Closed'),
    ], string="Status", default='new', tracking=True)

    time_in = fields.Datetime(string="Time In")
    time_out = fields.Datetime(string="Time Out")
    actual_release_date = fields.Date(string="Actual Release Date")
    downtime = fields.Float(string="Downtime (Hrs)", compute="_compute_downtime", store=True)
    expected_release_date = fields.Date(string="Expected Release Date")
    type = fields.Char(string="Type")
    make = fields.Char(string="Make")

    work_description = fields.Text(string="Description of Work & Root Cause")

    wrench_time_ids = fields.One2many('garage.job.card.wrench', 'job_card_id', string="Wrench Time")
    part_request_ids = fields.One2many('garage.job.card.part', 'job_card_id', string="Part Requests")
    sublet_work_ids = fields.One2many('garage.job.card.sublet', 'job_card_id', string="Sublet Work")

    driver_signature = fields.Binary(string="Driver Signature")
    road_test_done = fields.Boolean(string="Road Test Done")

    foreman_id = fields.Many2one('res.users', string="Foreman")
    foreman_sign_date = fields.Date(string="Foreman Date")
    pmv_manager_id = fields.Many2one('res.users', string="PMV Manager")
    pmv_sign_date = fields.Date(string="PMV Manager Date")
    service_id = fields.Many2one('fleet.vehicle.log.services', string="Related Service Log")
    mechanical_checklist_ids = fields.One2many(
        'garage.job.card.checklist.line', compute='_compute_section_checklists',
         readonly=False
    )
    lube_checklist_ids = fields.One2many(
        'garage.job.card.checklist.line', compute='_compute_section_checklists',
        readonly=False
    )
    mixer_checklist_ids = fields.One2many(
        'garage.job.card.checklist.line', compute='_compute_section_checklists',
         readonly=False
    )

    @api.depends('time_in', 'time_out')
    def _compute_downtime(self):
        for rec in self:
            if rec.time_in and rec.time_out:
                delta = rec.time_out - rec.time_in
                rec.downtime = delta.total_seconds() / 3600.0
            else:
                rec.downtime = 0.0

    @api.model
    def create(self, vals):
        if isinstance(vals, dict) and vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('garage.job.card') or 'New'

        job_card = super().create(vals)

        if vals.get('asset_id'):
            asset = self.env['fleet.vehicle'].browse(vals['asset_id'])
            category = asset.category_id.name.strip().lower() if asset.category_id else ''
            checklist = []

            if category == 'transit mixer a':
                checklist = job_card._load_checklist(_transit_mixer_a_data())
            elif category == 'transit mixer b':
                checklist = job_card._load_checklist(_transit_mixer_b_data())
            elif category == 'transit mixer c':
                checklist = job_card._load_checklist(_transit_mixer_c_data())
            elif category == 'boom pump a':
                checklist = job_card._load_checklist(_boom_bump_a_data())
            elif category == 'boom pump b':
                checklist = job_card._load_checklist(_boom_bump_b_data())
            elif category == 'boom pump c':
                checklist = job_card._load_checklist(_boom_bump_c_data())

            job_card.checklist_ids = checklist

        return job_card

    def print_job_cards(self):
        return self.env.ref('sdm_garage_services.report_job_card').report_action(self)

    def action_sync_to_service(self):
        for job in self:
            if job.asset_id and job.asset_id.category_id:
                incomplete_lines = job.checklist_ids.filtered(lambda line: not line.completed)
                if incomplete_lines:
                    raise UserError("Please complete all checklist items before syncing to service.")

            if not job.job_type_id or not job.job_type_id.fleet_service_type_id:
                raise UserError("Please link the Job Type to a Fleet Service Type before syncing to service.")

            service = job.service_id
            if not service:
                service = self.env['fleet.vehicle.log.services'].create({
                    'job_card': job.name,
                    'vehicle_id': job.asset_id.id,
                    'in_timestamp': job.time_in,
                    'out_timestamp': job.time_out,
                    'job_card_id': job.id,
                    'service_type_id': job.job_type_id.fleet_service_type_id.id,
                })
                job.service_id = service

            service.in_timestamp = job.time_in
            service.out_timestamp = job.time_out
            service.vehicle_id = job.asset_id.id
            service.service_type_id = job.job_type_id.fleet_service_type_id.id

            if job.time_in and job.time_out:
                delta = job.time_out - job.time_in
                service.wrench_time = round(delta.total_seconds() / 3600.0, 2)

            service.consumable_line_ids.unlink()

            for part in job.part_request_ids:
                product_name = part.product_no.name if hasattr(part.product_no, 'name') else str(part.product_no)
                product = self.env['product.product'].search([
                    ('name', 'ilike', product_name)
                ], limit=1)
                if not product:
                    raise UserError(f"Product with Part No '{product_name}' not found in Product Master.")

                self.env['fleet.vehicle.service.part.line'].create({
                    'service_id': service.id,
                    'product_id': product.id,
                    'quantity': part.quantity,
                    'usage_type': 'out',
                    'usage_reason': part.description,
                    'used_date': fields.Date.context_today(self),
                    'vehicle_id': job.asset_id.id,
                })

    def write(self, vals):
        res = super().write(vals)
        if 'asset_id' in vals:
            for job_card in self:
                asset = job_card.asset_id
                category = asset.category_id.name.strip().lower() if asset.category_id else ''
                checklist = []

                if category == 'transit mixer a':
                    checklist = job_card._load_checklist(_transit_mixer_a_data())
                elif category == 'transit mixer b':
                    checklist = job_card._load_checklist(_transit_mixer_b_data())
                elif category == 'transit mixer c':
                    checklist = job_card._load_checklist(_transit_mixer_c_data())
                elif category == 'boom pump a':
                    checklist = job_card._load_checklist(_boom_bump_a_data())
                elif category == 'boom pump b':
                    checklist = job_card._load_checklist(_boom_bump_b_data())
                elif category == 'boom pump c':
                    checklist = job_card._load_checklist(_boom_bump_c_data())

                job_card.checklist_ids = checklist
        return res

    @api.depends('checklist_ids')
    def _compute_section_checklists(self):
        for rec in self:
            rec.mechanical_checklist_ids = rec.checklist_ids.filtered(
                lambda line: line.section in ['Mechanical Checks / Inspection / Adjustments']
            )
            rec.lube_checklist_ids = rec.checklist_ids.filtered(
                lambda line: line.section in ['Lube & Fluids', 'Lube & Fluids/Filters']
            )
            rec.mixer_checklist_ids = rec.checklist_ids.filtered(
                lambda line: line.section in ['Mixer Units Checks / Inspection', 'Concrete Pumps']
            )

    @api.constrains('asset_id', 'time_in', 'time_out')
    def _check_vehicle_availability(self):
        for record in self:
            if not (record.asset_id and record.time_in and record.time_out):
                continue

            conflict_msgs = []
            overlapping_services = self.env['fleet.vehicle.log.services'].search([
                ('vehicle_id', '=', record.asset_id.id),
                ('state', '=', 'running'),
                ('in_timestamp', '<=', record.time_out),
                ('out_timestamp', '>=', record.time_in),
            ])
            if overlapping_services:
                msg = "\n".join([
                    f"• Service: {s.service_type_id.name} from {s.in_timestamp} to {s.out_timestamp}"
                    for s in overlapping_services
                ])
                conflict_msgs.append(("The vehicle is currently in Service:\n") + msg)

            if conflict_msgs:
                raise ValidationError("\n\n".join(conflict_msgs))

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        if self.asset_id and self.asset_id.category_id:
            category = self.asset_id.category_id.name.strip().lower()
            # self.checklist_ids = [(5, 0, 0)]
            if category == 'transit mixer a':
                self.checklist_ids = self._load_checklist(_transit_mixer_a_data())
            elif category == 'transit mixer b':
                self.checklist_ids = self._load_checklist(_transit_mixer_b_data())
            elif category == 'transit mixer c':
                self.checklist_ids = self._load_checklist(_transit_mixer_c_data())
            elif category == 'boom pump a':
                self.checklist_ids = self._load_checklist(_boom_bump_a_data())
            elif category == 'boom pump b':
                self.checklist_ids = self._load_checklist(_boom_bump_b_data())
            elif category == 'boom pump c':
                self.checklist_ids = self._load_checklist(_boom_bump_c_data())

    def _load_checklist(self, checklist):
        return [
            (0, 0, {
                'section': section,
                'name': item,
                'completed': False,
                'is_checked': False,
            })
            for section, items in checklist.items()
            for item in items
        ]

    def action_close_job_card(self):
        for rec in self:
            if not rec.time_out:
                raise UserError("Please set 'Time Out' before closing the job card.")
            rec.state = 'closed'
    def action_reopen_job_card(self):
        for rec in self:
            rec.state = 'running'


class GarageJobType(models.Model):
    _name = 'garage.job.type'
    _description = 'Garage Job Type'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    fleet_service_type_id = fields.Many2one(
        'fleet.service.type',
        string="Linked Fleet Service Type",
        help="This is used to sync Job Card with the fleet service log."
    )

class ProductTemplate(models.Model):
    _inherit = "product.template"

    vehicle_category = fields.Many2one('fleet.vehicle.model.category', string="Vehicle Category")

class FleetVehicleModelCategory(models.Model):
    _inherit = 'fleet.vehicle.model.category'
    _description = 'Category of the model'

    product_ids = fields.One2many(
        'product.template',
        'vehicle_category',
        string="Related Products"
    )
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_mechanic = fields.Boolean(string="Is Mechanic")

class GarageJobCardWrench(models.Model):
    _name = 'garage.job.card.wrench'
    _description = 'Wrench Time Entry'

    job_card_id = fields.Many2one('garage.job.card', string="Job Card")
    item = fields.Char(string="Item")
    mechanic_id = fields.Many2one('hr.employee', string="Mechanic/Technician", tracking=True,
        domain="[('is_mechanic', '=', True)]")
    tech_id = fields.Char(string="ID", related='mechanic_id.barcode', store=True, readonly=True)
    date = fields.Date(string="Date")
    start_time = fields.Datetime(string="Start Time")
    finish_time = fields.Datetime(string="Finish Time")
    time_spent = fields.Float(string="Time Spent (Hours)", compute="_compute_time_spent", store=True)

    @api.depends('start_time', 'finish_time')
    def _compute_time_spent(self):
        for rec in self:
            if rec.start_time and rec.finish_time and rec.finish_time > rec.start_time:
                delta = rec.finish_time - rec.start_time
                rec.time_spent = round(delta.total_seconds() / 3600, 2)
            else:
                rec.time_spent = 0.0


class GarageJobCardSublet(models.Model):
    _name = 'garage.job.card.sublet'
    _description = 'Sublet Work'

    job_card_id = fields.Many2one('garage.job.card', string="Job Card")
    date = fields.Date(string="Date")
    outlet = fields.Char(string="Outlet")
    component_description = fields.Char(string="Description")
    completion_time = fields.Datetime(string="Completion Time")
    duration_hours = fields.Float(string="Duration (Hrs)", compute="_compute_duration", store=True)
    maintenance_done = fields.Text(string="Maintenance Done")
    out_time = fields.Datetime(string="Out Time")
    in_time = fields.Datetime(string="In Time")
    cost = fields.Float(string="Cost (AED)")

    @api.depends('out_time', 'in_time')
    def _compute_duration(self):
        for rec in self:
            if rec.out_time and rec.in_time:
                delta = rec.in_time - rec.out_time
                rec.duration_hours = round(delta.total_seconds() / 3600, 2)
            else:
                rec.duration_hours = 0.0


class GarageJobCardPart(models.Model):
    _name = 'garage.job.card.part'
    _description = 'Job Card Part Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    job_card_id = fields.Many2one('garage.job.card', string="Job Card")
    mechanic_id = fields.Many2one('hr.employee', string="Mechanic" ,domain="[('is_mechanic', '=', True)]")
    foreman_id = fields.Many2one('res.users', string="Foreman")
    part_no = fields.Char(string="Part No.")
    spare_category_id = fields.Many2one('spare.part.category', string="Spare Part Category")
    storeman = fields.Many2one('res.users', string="Storeman")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('foreman_approved', 'Foreman Approved'),
        ('store_approved', 'Store Approved'),
        ('issued', 'Issued'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', tracking=True)
    product_no = fields.Many2one('product.template', string="Part Number.", domain=[])
    description = fields.Char(string="Description", readonly=True)
    quantity = fields.Integer(string="Qty")
    vehicle_category_id = fields.Many2one(
        'fleet.vehicle.model.category',
        string="Vehicle Category",
        related='job_card_id.asset_id.category_id',
        store=False
    )

    @api.onchange('spare_category_id')
    def _onchange_spare_category_id(self):
        if self.spare_category_id:
            self.description = self.spare_category_id.description
        else:
            self.description = False

    # @api.onchange('vehicle_category_id')
    # def _onchange_vehicle_category_id(self):
    #     if self.vehicle_category_id:
    #         return {
    #             'domain': {
    #                 'product_no': [('product_tmpl_id.vehicle_category.id', '=', self.vehicle_category_id.id)]
    #             }
    #         }
    #     else:
    #         return {'domain': {'product_no': []}}

    def action_submit_request(self):
        for rec in self:
            rec.state = 'requested'
            msg = f"Part request for {rec.product_no.name} submitted by {self.env.user.name}."
            rec.message_post(body=msg)
            if rec.job_card_id:
                rec.job_card_id.message_post(
                    body=f"[Part Request] {msg}",
                    subtype_xmlid='mail.mt_note'
                )

    def action_foreman_approve(self):
        for rec in self:
            if not self.env.user.has_group('sdm_garage_services.group_foreman'):
                raise AccessError("Only users in the Foreman group can approve.")

            if not rec.foreman_id:
                raise UserError("Please assign a Foreman before approving.")
            if rec.foreman_id.id != self.env.user.id:
                raise AccessError("Only the assigned Foreman can approve this request.")

            rec.state = 'foreman_approved'
            msg = f"Foreman {self.env.user.name} approved part request for {rec.product_no.name}."
            rec.message_post(body=msg)
            if rec.job_card_id:
                rec.job_card_id.message_post(
                    body=f"[Foreman Approval] {msg}",
                    subtype_xmlid='mail.mt_note'
                )

    def action_store_approve(self):
        for rec in self:
            if not self.env.user.has_group('sdm_garage_services.group_storeman'):
                raise AccessError("Only users in the Storeman group can approve.")

            if not rec.storeman:
                raise UserError("Please assign a Storeman before approving.")
            if rec.storeman.id != self.env.user.id:
                raise AccessError("Only the assigned Storeman can approve this request.")

            rec.state = 'store_approved'
            msg = f"Store Manager {self.env.user.name} approved part request for {rec.product_no.name}."
            rec.message_post(body=msg)
            if rec.job_card_id:
                rec.job_card_id.message_post(
                    body=f"[Store Approval] {msg}",
                    subtype_xmlid='mail.mt_note'
                )

    def action_issue_part(self):
        for rec in self:
            if not self.env.user.has_group('sdm_garage_services.group_storeman'):
                raise AccessError("Only users in the Storeman group can issue parts.")

            if rec.state != 'store_approved':
                raise UserError("Store Manager must approve before issuing.")
            if not rec.storeman or rec.storeman.id != self.env.user.id:
                raise AccessError("Only the assigned Storeman can issue this part.")

            rec.state = 'issued'
            msg = f"Part {rec.product_no.name} has been issued from store by {self.env.user.name}."
            rec.message_post(body=msg)
            if rec.job_card_id:
                rec.job_card_id.message_post(
                    body=f"[Part Issued] {msg}",
                    subtype_xmlid='mail.mt_note'
                )

    def action_reject(self):
        for rec in self:
            if not self.env.user.has_group('sdm_garage_services.group_foreman') and not self.env.user.has_group(
                    'sdm_garage_services.group_storeman'):
                raise AccessError("Only Foreman or Storeman can reject this request.")

            if not rec.storeman and not rec.foreman_id:
                raise UserError("Please assign a Foreman or Storeman to reject.")
            if self.env.user.id not in (rec.storeman.id, rec.foreman_id.id):
                raise AccessError("Only the assigned Foreman or Storeman can reject this request.")

            rec.state = 'rejected'
            msg = f"Part request for {rec.product_no} was rejected by {self.env.user.name}."
            rec.message_post(body=msg)
            if rec.job_card_id:
                rec.job_card_id.message_post(
                    body=f"[Part Rejected] {msg}",
                    subtype_xmlid='mail.mt_note'
                )


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    job_card_id = fields.Many2one('garage.job.card', string="Related Job Card")
    job_card = fields.Char(string="Related Job Card")

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

class GarageJobCardChecklistLine(models.Model):
    _name = 'garage.job.card.checklist.line'
    _description = 'Job Card Checklist Line'

    job_card_id = fields.Many2one('garage.job.card', string="Job Card", required=True, ondelete="cascade")
    name = fields.Char(string="Checklist Item")
    is_checked = fields.Boolean(string="Checked")
    section = fields.Char(string="Section")
    completed = fields.Boolean(string="Completed")

def _transit_mixer_a_data():
    return {
        "Mechanical Checks / Inspection / Adjustments": [
            "Wheel Nuts for Security", "Road Springs And U Bolts", "Steering Joint and linkages",
            "Wheel Bearings and King Pins", "Electrical Functions", "Check for Air / Oil / Water Leaks",
            "Cab / Mountings / Tilt And Lock Mechanism", "Wheel Brakes / Service / Parking / Slack Adjusters / Warning Devices",
            "Check / Adjust All V Belts", "Clutch Operation / Wear", "Drain Air Tanks of Condensate / Contamination",
            "A/C System Checks  Clean / Replace Filter", "Check Gearbox / Axle Breathers",
            "Check / Adjust Engine R.P.M ( Remote Operation )", "Check Tyre Condition / Inflation"
        ],
        "Lube & Fluids": [
            "Change Engine Oil and Filter", "Change Diesel  Filters / Water Separator", "Change Steering Oil  Filter",
            "Change Gearbox / Hubs / Axle Oils", "Clean / Replace Main Air Filter", "Change Dry Air Filter",
            "Change Coolant Filter", "Check  Coolant Level", "Grease Steering Joints / King Pins",
            "Grease Prop shaft's / Centre Bearings", "Grease Brake Camshafts / Slack Adjusters",
            "Lubricate Clutch / Throttle / Brake Linkages", "Lubricate Cab Door  Hinges / Locks",
            "Check Battery Electrolyte and Terminals"
        ],
        "Mixer Units Checks / Inspection": [
            "Change Engine Oil  and Filters", "Change Diesel  Filters", "Change Gearbox Oil",
            "Change Hydraulic Oil & Filter", "Clean / Replace Air Filter", "Clean Oil Bath",
            "Grease Drum Rollers / Ring / Swivel / Chute", "Grease PTO Prop shaft", "Check Mounting  Bolts For Tightness",
            "Check Drum Rotation Speed ( 14 - 16  RPM )", "Lubricate Remote Operation",
            "Check the drum blades  & Caps for wear", "Check the concrete build up.", "Check extention chute Condition",
            "Check V- Shape  Discharge Chute"
        ]
    }

def _transit_mixer_b_data():
    return {
        "Mechanical Checks / Inspection / Adjustments": _transit_mixer_a_data()["Mechanical Checks / Inspection / Adjustments"],
        "Lube & Fluids": _transit_mixer_a_data()["Lube & Fluids"] + [
            "Renew Wheel Bearing Grease"
        ],
        "Mixer Units Checks / Inspection": _transit_mixer_a_data()["Mixer Units Checks / Inspection"]
    }

def _transit_mixer_c_data():
    return _transit_mixer_b_data()

def _boom_bump_a_data():
    return {
        "Mechanical Checks / Inspection / Adjustments": [
            "Wheel Nuts for Security", "Road Springs And U Bolts", "Steering Joint and linkages",
            "Wheel Bearings and King Pins", "Wheel Brakes / Service / Parking / Slack Adjusters / Warning Devices",
            "Electrical Functions", "Cab / Mountings / Tilt And Lock Mechanism", "Check for Air / Oil / Water Leaks",
            "Check / Adjust All V Belts", "Clutch Operation / Wear", "Drain Air Tanks of Condensate / Contamination",
            "A/C System Checks Clean / Replace Filter", "Check Gearbox / Axle Breathers", "Check Tyre Condition / Inflation"
        ],
        "Lube & Fluids/Filters": [
            "Change Engine Oil and Filter", "Change Diesel Filters / Water Separator", "Check Steering Oil Level",
            "Check Gearbox / Hubs / Axle Oils Level", "Clean / Replace Main Air Filter", "Check Coolant Level",
            "Grease Steering Joints / King Pins", "Grease Prop shaft's / Centre Bearings",
            "Grease Brake Camshafts / Slack Adjusters", "Lubricate Clutch / Throttle / Brake Linkages",
            "Lubricate Cab Door Hinges / Locks", "Check Battery Electrolyte and Terminals"
        ],
        "Concrete Pumps": [
            "Check Hydraulic Oil Level", "Check Transfer Box Oil Level", "Check Agitator G/Box Oil Level",
            "Check Compressor Oil Level", "Check Slewing G/Box Oil Level", "Grease PTO Prop Shaft",
            "Grease Boom Pins /Bushes", "Grease Agitator / Rock Valve", "Grease Outrigger Rollers",
            "Grease Slewing Ring / Pedestal", "Rotate Cutting Ring (Schwing)", "Rotate Boom Pipes"
        ]
    }

def _boom_bump_b_data():
    return _boom_bump_a_data()

def _boom_bump_c_data():
    return _boom_bump_a_data()


