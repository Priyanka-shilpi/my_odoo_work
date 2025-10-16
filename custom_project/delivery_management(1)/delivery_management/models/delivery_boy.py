from odoo import models, fields, api
from odoo.exceptions import UserError



class DeliveryBoy(models.Model):
    _name = 'delivery.boy'
    _description = 'Delivery Boy'

    name = fields.Char(required=True)
    email = fields.Char(string="Email Address")
    partner_id = fields.Char(string="Related Partner")
    image = fields.Binary()
    state = fields.Selection([
        ('draft', 'Never Connected'),
        ('confirmed', 'Confirmed')
    ], string='Status', default='draft')

    group_count = fields.Integer(string="Group Count", )
    access_count = fields.Integer(string="Access Count", )
    rule_count = fields.Integer(string="Rule Count", )

    is_delivery_boy = fields.Boolean(string="Is Delivery Boy", default=True)
    multi_companies = fields.Char("Multi Companies")

    allowed_companies = fields.Char(string="Allowed Companies", compute='_compute_company_info', store=True)
    default_companies = fields.Char(string="Default Company", compute='_compute_company_info', store=True)

    usertype = fields.Char("User Type")
    user_type = fields.Selection([
        ('internal', 'Internal User'),
        ('portal', 'Portal'),
        ('public', 'Public')
    ], string="User Types", default='portal')

    national_id = fields.Char(string="National ID")
    mobile = fields.Char(string="Mobile")
    transportation = fields.Selection([
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('truck', 'Truck'),
    ], string="Transportation",)
    commission_fee = fields.Float(string="Commission Fees")

    # def send_email(self):
    #     pass

    def dummy_method_groups(self):
        pass

    def dummy_method_access(self):
        pass

    def dummy_method_rules(self):
        pass

    @api.depends('name')
    def _compute_company_info(self):
        companies = self.env['res.company'].search([])
        allowed = ', '.join(comp.name for comp in companies)
        default = self.env.company.name
        for rec in self:
            rec.allowed_companies = allowed
            rec.default_companies = default

    @api.constrains('mobile')
    def _check_mobile_number(self):
        for record in self:
            if record.mobile:
                if len(record.mobile) != 10 or not record.mobile.isdigit():
                    raise UserError("The mobile number must be exactly 10 digits and contain no characters.")


