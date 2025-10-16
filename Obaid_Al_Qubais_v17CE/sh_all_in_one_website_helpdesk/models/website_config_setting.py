# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api


class Website(models.Model):
    _inherit = 'website'

    google_recaptcha = fields.Boolean(string=" Google reCAPTCHA ? ")
    site_key = fields.Char(string=" Site Key ")
    secret_key = fields.Char(string=" Secret Key ")
    attachment_size = fields.Integer(string="Ticket Attachment Filesize (KB)")
    website_helpdesk_visibility = fields.Selection([   
        ('public', 'Public'),
        ('login', 'Log in ')
        ],string='Website Helpdesk Visibility')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_recaptcha = fields.Boolean(
        string="Google reCAPTCHA ?", related='website_id.google_recaptcha', readonly=False)
    site_key = fields.Char(
        string=" Site Key ", related='website_id.site_key', readonly=False)
    secret_key = fields.Char(
        string=" Secret Key ", related='website_id.secret_key', readonly=False)
    attachment_size = fields.Integer(
        string="Ticket Attachment Filesize (KB)", related='website_id.attachment_size', readonly=False)
    
    website_helpdesk_visibility = fields.Selection(related='website_id.website_helpdesk_visibility',string='Website Helpdesk Visibility',readonly=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.default'].set(
            'res.config.settings', 'google_recaptcha', self.google_recaptcha)
        self.env['ir.default'].set(
            'res.config.settings', 'site_key', self.site_key)
        self.env['ir.default'].set(
            'res.config.settings', 'secret_key', self.secret_key)
        self.env['ir.default'].set(
            'res.config.settings', 'attachment_size', self.attachment_size)

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     res.update(
    #         attachment_size=self.env['ir.default'].get(
    #             'res.config.settings', 'attachment_size'),
    #     )
    #     return res
