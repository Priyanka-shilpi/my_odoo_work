from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class AllcationRequest(models.Model):
    _name = 'allcation.request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'

    @api.model
    def default_warehouse_id(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)],limit=1)
        return warehouse and warehouse.id

    name = fields.Char(readonly=True)
    subject = fields.Char(required=True)
    category_id = fields.Many2one('maintenance.equipment.category' , string='Category')
    allcation_type = fields.Selection([('office','Office'),('third','Third Party')] , default='office')
    allcation_in = fields.Selection([('inoffice','In-office'),('remote','Remote')], string="Allocation", default='inoffice')
    third_party = fields.Selection([('rent','Rent'),('lease','Lease')], default='rent', string="Third Party")
    equipment_id = fields.Many2one('maintenance.equipment' ,string='Equipment')
    product_id = fields.Many2one('product.product', string='Product')
    serial_id = fields.Many2one('stock.lot' , string='Lot No')
    scheduled_date = fields.Datetime('Scheduled Date' ,default=datetime.today())
    priority = fields.Selection([('0','Very Low'),('1','Low'),('2','Normal'),('3','High')])
    assing_to = fields.Many2one('hr.employee', string='Assigned To', required=True,tracking=True, default=lambda self:self.env.user.employee_id)
    create_date = fields.Datetime(string='Create Date', default=fields.Date.today())
    create_by = fields.Many2one('res.users',string='Create By', default=lambda self: self.env.user)
    approve_by = fields.Many2one('res.users', string='Approved By', tracking=True)
    approve_date = fields.Datetime(string='Approved Date')
    state = fields.Selection([('new','New'),('waitapprove','Waiting For Approval'),('approve','Approved'),('allocate','Allocated'),('return','Return'),('trans','Transfer'),('cancel','Cancel')], default='new', string='State',tracking=True)
    note = fields.Text(string="Note")
    # damage_ids = fields.One2many('damage.details.line','allocation_id')
    allocation_id = fields.Many2one('allcation.request')
    allocation_count = fields.Integer(string="Allocations", compute="_compute_allocation_count")
    transfer = fields.Boolean()
    department_id = fields.Many2one('hr.department' ,string="Department")
    job_positions =fields.Many2one('hr.job' ,string="Job Postions")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", default=default_warehouse_id)
    sources_id = fields.Many2one('stock.location' ,string="Sources")
    destination_id = fields.Many2one('stock.location' ,string="Destination")
    picking_ids = fields.One2many('stock.picking', 'allocation_id', string="Pickings")
    picking_count = fields.Integer(string="Picking", compute="_compute_picking_count")


    def _compute_picking_count(self):
        for picking in self:
            picking.picking_count = self.env['stock.picking'].search_count([('allocation_id','=', self.id)])
    
    def action_picking(self):
        picking_ids: self.env['stock.picking'].search([('allocation_id', '=', self.id)])
        return {
            'name': _('Pickings'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.picking_ids.ids)],
        }

    @api.onchange('equipment_id')
    def _onchange_equipment(self):
        if self.equipment_id:
            self.product_id = self.equipment_id.product_id.id

    @api.onchange('warehouse_id')
    def _onchange_werehouse_location(self):
        if self.warehouse_id:
            self.sources_id = self.warehouse_id.lot_stock_id
            self.destination_id = self.warehouse_id.equipment_location_id

    @api.onchange('assing_to')
    def onchange_product_id(self):
        if self.assing_to:
            self.department_id = self.assing_to.department_id
            self.job_positions = self.assing_to.job_id


    def _compute_allocation_count(self):
        for allocate in self:
            allocate.allocation_count = self.env['allcation.request'].search_count([('allocation_id','=', self.id)])
    

    def action_open_allocatin(self):
        allocation_ids = self.env['allcation.request'].search([('allocation_id', '=', self.id)])
        return {
            'name': _('Allocations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'allcation.request',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', allocation_ids.ids)],
        }
    

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('allcation.request') or 'New'
        return super(AllcationRequest, self).create(vals)

    def button_submit(self):
        template_id = self.env.ref('pways_equipment_all_in_one.email_template_allocation_request').id
        email_template_id = self.env['mail.template'].sudo().browse(template_id)
        email_template_id.send_mail(self.id)
        msg_body = _('mail is send to manager for approval.')
        self.message_post(body=msg_body)
        self.state = 'waitapprove'

    def button_draf(self):
        self.state = "new"

    def button_approve(self):
        self.approve_by = self.env.user.id
        self.approve_date = fields.Date.today()
        self.state = "approve"

    def make_picking_out(self):
        data = self.warehouse_id and self.destination_id and self.sources_id
        if not data:
            raise ValidationError(_('Warehouse or source or destination location not define'))
        lines = []
        return_move_id = (0, 0 , {
            'name': self.name,
            'origin': self.name,
            'product_id': self.product_id.id,
            'location_id': self.sources_id.id,
            'location_dest_id':  self.destination_id.id,
            'product_uom_qty': 1,
            'product_uom': self.product_id.uom_id.id,
            'picking_type_id' : self.warehouse_id.out_type_id.id
        })
        lines.append(return_move_id)
        picking_id = self.env['stock.picking'].create({
                    'partner_id': self.create_by.partner_id.id, 
                    'location_id':  self.sources_id.id,
                    'location_dest_id': self.destination_id.id,
                    'picking_type_id': self.warehouse_id.out_type_id.id,
                    'allocation_id': self.id,
                    'origin': self.name,
                    'move_ids': lines,
                })
        picking_id.action_confirm()
        return picking_id

    def button_allocate(self):
        if self.approve_by and self.assing_to:
            template_id = self.env.ref('pways_equipment_all_in_one.email_template_allocation_request').id
            email_template_obj = self.env['mail.template'].sudo().browse(template_id)
            
            # values = email_template_obj._generate_template(self.id, ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
            values = email_template_obj._generate_template([self.id], ['attachment_ids','auto_delete','body_html','email_cc','email_from','email_to','mail_server_id','model','partner_to','reply_to','report_template_ids','res_id','scheduled_date','subject'])
            values  = values.get(self.id)
            values.pop('attachments', False)
            # print('values..................................', values) 

            values['recipient_ids'] = [Command.link(pid) for pid in values.get('partner_ids', list())]
            values['email_from'] = self.create_by.partner_id.email
            values['email_to'] = self.assing_to.work_email
            values['res_id'] = self.id
            values['author_id'] = self.create_by.partner_id.id

            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.create(values)
            if msg_id:
                mail_mail_obj.send(msg_id)

            msg_body = _('mail is sent to the manager for approval.')
            self.message_post(body=msg_body)
            self.make_picking_out()
            self.equipment_id.write({'employee_id' : self.assing_to.id, 'equipment_status': 'occupy'})
            self.state = "allocate"
      
    # def return_picking(self):
    #     for picking in self.picking_ids:
    #         returned_moves = self.env['stock.move'].search([('origin_returned_move_id.picking_id', '=', picking.id), ('state', '!=', 'cancel')])
    #         if returned_moves:
    #             raise ValidationError(_('Return already create for %s', picking.name))
    #         vals = {'picking_id': picking.id, 'location_id' : picking.location_id.id}
    #         return_picking_wizard = self.env['stock.return.picking'].with_context(active_id=picking.id).create(vals)
    #         return_lines = []
    #         for line in picking.move_lines:
    #             return_line = self.env['stock.return.picking.line'].create({   
    #                     'product_id': line.product_id.id, 
    #                     'quantity': line.quantity_done, 
    #                     'wizard_id': return_picking_wizard.id,
    #                     'move_id': line.id})
    #             return_lines.append(return_line.id)
    #         return_picking_wizard.write({'product_return_moves': [(6, 0, return_lines)]})
    #         new_picking_id, pick_type_id = return_picking_wizard._create_returns()
    #         new_picking_ids = self.env['stock.picking'].browse(new_picking_id)
    #         new_picking_ids.action_assign()
    #     return True

    def button_return(self):
        for picking in self.picking_ids:
            returned_moves = self.env['stock.move'].search([('origin_returned_move_id.picking_id', '=', picking.id), ('state', '!=', 'cancel')])
            if returned_moves:
                raise ValidationError(_('Return already create for %s', picking.name))
            vals = {'picking_id': picking.id}
            return_picking_wizard = self.env['stock.return.picking'].with_context(active_id=picking.id).create(vals)
            return_lines = []
            for line in picking.move_ids:
                return_line = self.env['stock.return.picking.line'].create({   
                        'product_id': line.product_id.id, 
                        # 'quantity': line.quantity_done, 
                        'quantity': line.quantity, 
                        'wizard_id': return_picking_wizard.id,
                        'move_id': line.id})
                return_lines.append(return_line.id)
            return_picking_wizard.write({'product_return_moves': [(6, 0, return_lines)]})
            new_picking_ids= return_picking_wizard._create_return()
            new_picking_ids.action_assign()

        # lines = []
        # return_move_id = (0, 0 , {
        #     'name': self.name,
        #     'origin': self.name,
        #     'product_id': self.product_id.id,
        #     'location_id': self.destination_id.id, 
        #     'location_dest_id': self.sources_id.id,
        #     'product_uom_qty': 1,
        #     'product_uom': self.product_id.uom_id.id,
        #     'picking_type_id' : self.warehouse_id.in_type_id.id
        # })
        # lines.append(return_move_id)
        # picking_id = self.env['stock.picking'].create({
        #             'partner_id': self.create_by.partner_id.id, 
        #             'location_id': self.destination_id.id,
        #             'location_dest_id': self.sources_id.id,
        #             'picking_type_id': self.warehouse_id.in_type_id.id,
        #             'allocation_id': self.id,
        #             'origin': self.name,
        #             'move_lines': lines,
        #         })

        self.equipment_id.write({'employee_id' : False, 'equipment_status': 'free'})
        self.state = "return"

    def button_cancel(self):
        self.state = "cancel"

