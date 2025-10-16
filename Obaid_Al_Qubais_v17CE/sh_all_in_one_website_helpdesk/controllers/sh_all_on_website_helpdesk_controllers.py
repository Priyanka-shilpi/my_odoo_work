# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import http
from odoo.http import request
import json
import base64


class HelpdeskTicketController(http.Controller):

    @http.route([
        '/helpdesk',
    ], type='http', auth="public", methods=['GET'], website=True, csrf=False)
    def helpdesk(self, **post):
        if request.website.website_helpdesk_visibility == 'login' and not request.session.uid:
            return request.redirect('/web/login?redirect=/helpdesk')
        # google_recaptcha = request.env['ir.default'].get('res.config.settings', 'google_recaptcha')
        google_recaptcha = False
        # google_captcha_site_key = request.env['ir.default'].get('res.config.settings', 'site_key')
        google_captcha_site_key = False
        # ticket_attachment_size = request.env['ir.default'].get('res.config.settings', 'attachment_size')
        ticket_attachment_size = 1200
        if ticket_attachment_size == None:
            ticket_attachment_size = 0
        return request.render("sh_all_in_one_website_helpdesk.helpdesk_form", {'google_recaptcha': google_recaptcha, 'google_captcha_site_key': google_captcha_site_key, 'file_size': ticket_attachment_size})

    @http.route('/subcategory-data', type="json", auth="public", website=True, csrf=False)
    def sub_category_data(self, **kw):
        dic = {}
        if kw.get('category_id'):
            sub_categ_list = []            
            sub_categ_ids = request.env['helpdesk.subcategory'].sudo().search([('parent_category_id', '=', int(kw.get('category_id')))])
            for sub in sub_categ_ids:
                sub_categ_dic = {
                    'id': sub.id,
                    'name': sub.name,
                }
                sub_categ_list.append(sub_categ_dic)
            dic.update({
                'sub_categories': sub_categ_list
            })
        return json.dumps(dic)

    @http.route('/ticket-data', type="http", auth="public", website=True, csrf=False)
    def ticket_data(self, **kw):
        dic = {}
        if request.env.user and request.env.user.login != 'public':
            dic.update({
                'login_user': '1'
            })
            if request.env.user.partner_id:
                if request.env.user.partner_id.name:
                    dic.update({
                        'name': request.env.user.partner_id.name,
                    })
                if request.env.user.partner_id.email:
                    dic.update({
                        'email': request.env.user.partner_id.email,
                    })
                if request.env.user.partner_id.mobile:
                    dic.update({
                        'mobile': request.env.user.partner_id.mobile or '',
                    })
        else:
            dic.update({
                'login_user': '0',
            })
        return json.dumps(dic)

    @http.route('/check-validation', type="http", auth="public", website=True, csrf=False)
    def check_validation(self, **kw):
        dic = {}
        if kw.get('contact_name') == '':
            dic.update({
                'name_msg': 'Name is Required.'
            })
        if kw.get('email') == '':
            dic.update({
                'email_msg': 'Email is Required.'
            })
        if kw.get('mobile') == '':
            dic.update({
                'mobile_msg': 'Mobile is Required.'
            })

        if request.website.google_recaptcha and kw.get('recaptcha') == '':
            dic.update({
                'recaptcha_msg': 'Captcha Required.'
            })
        return json.dumps(dic)

    @http.route('/helpdesk/ticket/process', type="http", auth="public", website=True, csrf=False)
    def helpdesk_process_ticket(self, **kwargs):
        if kwargs:
            values = {}
            # google_recaptcha = request.env['ir.default'].get(
            #     'res.config.settings', 'google_recaptcha')
            values = {}
            for field_name, field_value in kwargs.items():
                values[field_name] = field_value
            
            # if google_recaptcha:
            #     google_captcha_site_key = request.env['ir.default'].get(
            #         'res.config.settings', 'site_key')
            #     # Redirect them back if they didn't answer the captcha
            #     if 'g-recaptcha-response' not in values:
            #         return werkzeug.utils.redirect("/helpdesk")

            #     payload = {'secret': google_captcha_site_key,
            #                'response': str(values['g-recaptcha-response'])}
            #     requests.post(
            #         "https://www.google.com/recaptcha/api/siteverify", data=payload)
            
            login_user = request.env.user
            if login_user and login_user.login != 'public':
                partner_id = request.env['res.partner'].sudo().search(
                    [('email', '=', kwargs.get('email'))], limit=1)
                if not partner_id:
                    partner_id = request.env['res.partner'].sudo().create({
                        'name': kwargs.get('contact_name'),
                        'company_type': 'person',
                        'email': kwargs.get('email'),
                        'mobile': kwargs.get('mobile')
                    })
                if partner_id:
                    ticket_dic = {'partner_id': partner_id.id,
                                  'ticket_from_website': True}
                    if login_user.sh_portal_user_access and request.env.user.has_group('base.group_portal') and login_user.sh_portal_user_access == 'user' or login_user.sh_portal_user_access == 'manager' or login_user.sh_portal_user_access == 'leader':
                        if request.website.sudo().company_id.sh_default_team_id:
                            ticket_dic.update({
                                'team_id': request.website.sudo().company_id.sh_default_team_id.id,
                                'team_head': request.website.sudo().company_id.sh_default_team_id.team_head.id,
                                'user_id': request.website.sudo().company_id.sh_default_user_id.id,
                            })
                        else:
                            team_id = request.env['sh.helpdesk.team'].sudo().search(
                                ['|', ('team_head', '=', login_user.id), ('team_members', 'in', [login_user.id])])
                            if team_id:
                                ticket_dic.update({
                                    'team_id': team_id[-1].id,
                                    'team_head': team_id[-1].team_head.id,
                                    'user_id': login_user.id,
                                })
                            else:
                                ticket_dic.update({
                                    'user_id': login_user.id,
                                })
                    else:
                        if request.website.sudo().company_id.sh_default_team_id:
                            ticket_dic.update({
                                'team_id': request.website.sudo().company_id.sh_default_team_id.id,
                                'team_head': request.website.sudo().company_id.sh_default_team_id.team_head.id,
                                'user_id': request.website.sudo().company_id.sh_default_user_id.id,
                            })
                        else:
                            if not login_user.has_group('base.group_portal') and not login_user.sh_portal_user_access:
                                team_id = request.env['sh.helpdesk.team'].sudo().search(
                                    ['|', ('team_head', '=', login_user.id), ('team_members', 'in', [login_user.id])])
                                if team_id:
                                    ticket_dic.update({
                                        'team_id': team_id[-1].id,
                                        'team_head': team_id[-1].team_head.id,
                                        'user_id': login_user.id,
                                    })
                                else:
                                    ticket_dic.update({
                                        'user_id': login_user.id,
                                    })
                    if kwargs.get('contact_name'):
                        ticket_dic.update({
                            'person_name': kwargs.get('contact_name'),
                        })
                    if kwargs.get('email'):
                        ticket_dic.update({
                            'email': kwargs.get('email'),
                        })
                    if kwargs.get('mobile'):
                        ticket_dic.update({
                            'mobile_no': kwargs.get('mobile')
                        })
                    if kwargs.get('category'):
                        ticket_dic.update({
                            'category_id': int(kwargs.get('category')),
                        })
                    if kwargs.get('subcategory'):
                        ticket_dic.update({
                            'sub_category_id': int(kwargs.get('subcategory')),
                        })
                    if kwargs.get('subject'):
                        ticket_dic.update({
                            'subject_id': int(kwargs.get('subject')),
                        })
                    if kwargs.get('description'):
                        ticket_dic.update({
                            'description': kwargs.get('description'),
                        })
                    if kwargs.get('priority'):
                        ticket_dic.update({
                            'priority': int(kwargs.get('priority')),
                        })
                    ticket_dic.update({'state': 'customer_replied'})
                    ticket_id = request.env['sh.helpdesk.ticket'].sudo().create(
                        ticket_dic)
                    if 'file' in request.params:
                        attachment_ids = []
                        attached_files = request.httprequest.files.getlist(
                            'file')
                        for attachment in attached_files:
                            result = base64.b64encode(attachment.read())
                            attachment_id = request.env['ir.attachment'].sudo().create({
                                'name': attachment.filename,
                                'res_model': 'sh.helpdesk.ticket',
                                'res_id': ticket_id.id,
                                'display_name': attachment.filename,
                                'datas': result,
                            })
                            attachment_ids.append(attachment_id.id)
                        ticket_id.attachment_ids = [(6, 0, attachment_ids)]
            else:
                partner_id = request.env['res.partner'].sudo().search(
                    [('email', '=', kwargs.get('email'))], limit=1)
                if not partner_id:
                    partner_id = request.env['res.partner'].sudo().create({
                        'name': kwargs.get('contact_name'),
                        'company_type': 'person',
                        'email': kwargs.get('email'),
                        'mobile': kwargs.get('mobile'),
                    })
                if partner_id:
                    ticket_dic = {'partner_id': partner_id.id, 'ticket_from_website': True,
                                  'company_id': request.website.sudo().company_id.id}
                    if kwargs.get('contact_name'):
                        ticket_dic.update({
                            'person_name': kwargs.get('contact_name'),
                        })
                    if kwargs.get('email'):
                        ticket_dic.update({
                            'email': kwargs.get('email'),
                        })
                    if kwargs.get('mobile'):
                        ticket_dic.update({
                            'mobile_no': kwargs.get('mobile')
                        })
                    if kwargs.get('category'):
                        ticket_dic.update({
                            'category_id': int(kwargs.get('category')),
                        })
                    if kwargs.get('subcategory'):
                        ticket_dic.update({
                            'sub_category_id': int(kwargs.get('subcategory')),
                        })
                    if kwargs.get('subject'):
                        ticket_dic.update({
                            'subject_id': int(kwargs.get('subject')),
                        })
                    if kwargs.get('description'):
                        ticket_dic.update({
                            'description': kwargs.get('description'),
                        })
                    if kwargs.get('priority'):
                        ticket_dic.update({
                            'priority': int(kwargs.get('priority')),
                        })
                    ticket_dic.update({'state': 'customer_replied'})
                    ticket_id = request.env['sh.helpdesk.ticket'].sudo().create(
                        ticket_dic)
                    if 'file' in request.params:
                        attachment_ids = []
                        attached_files = request.httprequest.files.getlist(
                            'file')
                        for attachment in attached_files:
                            result = base64.b64encode(attachment.read())
                            attachment_id = request.env['ir.attachment'].sudo().create({
                                'name': attachment.filename,
                                'res_model': 'sh.helpdesk.ticket',
                                'res_id': ticket_id.id,
                                'display_name': attachment.filename,
                                'datas': result,
                            })
                            attachment_ids.append(attachment_id.id)
                        ticket_id.attachment_ids = [(6, 0, attachment_ids)]
            return http.request.render('sh_all_in_one_website_helpdesk.helpdesk_thank_you', {'success_msg': 'Your ticket '+str(ticket_id.name) + ' has been sent successfully.'})
        else:
            return http.request.render('sh_all_in_one_website_helpdesk.helpdesk_thank_you', {'error_msg': 'Please Go to out support page.', })
