from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pytz
import calendar

class StockMove(models.Model):
    _inherit = 'stock.move'

    request_id = fields.Many2one('maintenance.request', check_company=True)

class AccountMove(models.Model):
    _inherit = 'account.move'

    request_id = fields.Many2one('maintenance.request', check_company=True)

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    request_id = fields.Many2one('maintenance.request', check_company=True)

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    asset_tag_id = fields.Many2one('asset.tag.master')


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    recurring_type = fields.Many2one('work.schedule', string='Recurring Work Type')
    product_id = fields.Many2one('product.product',string="Product" )
    serial_id = fields.Many2one('stock.lot',string="Lot" )
    checklist_ids = fields.One2many('camp.asset.checklist.line','equipment_id')
    equipment_status = fields.Selection([('free','Free'),('occupy','Occupy'), ('maintenance','Maintenance')], default='free',string='Status')

    @api.onchange('recurring_type')
    def onchange_recurring_type_id(self):
        if self.recurring_type:
            self.period = self.recurring_type.days

    def dayNameFromWeekday(self, weekday):
        if weekday == 0:
            weeks = calendar.TextCalendar(calendar.MONDAY)
            return weeks
        if weekday == 1:
            weeks = calendar.TextCalendar(calendar.TUESDAY)
            return weeks
        if weekday == 2:
            weeks = calendar.TextCalendar(calendar.WEDNESDAY)
            return weeks
        if weekday == 3:
            weeks = calendar.TextCalendar(calendar.THURSDAY)
            return weeks
        if weekday == 4:
            weeks = calendar.TextCalendar(calendar.FRIDAY)
            return weeks
        if weekday == 5:
            weeks = calendar.TextCalendar(calendar.SATURDAY)
            return weeks
        if weekday == 6:
            weeks = calendar.TextCalendar(calendar.SUNDAY)
            return weeks

    # Total Public Holiday In Month
    def get_public_holidays_dates(self, next_action_date, next_action_date1):
        public_holidays_date = []
        total_holiday_date = []
        public_holidays_ids = self.env['resource.calendar.leaves'].search([
            ('date_from', '>=', next_action_date),
            ('date_to', '<=', next_action_date1),
            ('resource_id', '=',False)])
        
        for holiday in public_holidays_ids:
            curr_date = holiday.date_from.date()
            end_date = holiday.date_to.date()
            while curr_date <= end_date:
                public_holidays_date.append(curr_date.strftime("%Y-%m-%d"))
                curr_date += timedelta(days=1)
        
        for holiday in public_holidays_date:
            total_holiday_date.append(datetime.strptime(holiday, '%Y-%m-%d').date())
        return total_holiday_date

    # Employee Weekoff
    def get_employee_weekoff(self, employee_id, next_action_date, next_action_date1):
        weekoff_date = []
        final_weekoff = []
        year = next_action_date.year
        month = next_action_date.month
        total_days = [0,1,2,3,4,5,6]
        
        weekdays_id = set(employee_id.resource_calendar_id.attendance_ids.mapped('dayofweek'))
        total_weekday = list(weekdays_id)
        res = [eval(i) for i in total_weekday]
        weekoff = [x for x in total_days if x not in res]

        for week in weekoff:
            weeks = self.dayNameFromWeekday(week)
            for wekday in weeks.itermonthdays(year,month):
                if wekday != 0:
                    day = date(year,month,wekday)
                    if day.weekday() == week:
                        first_day = (str(year) + "-" + str(month) + "-" + str(wekday))
                        first_date = datetime.strptime(first_day, '%Y-%m-%d').date()
                        weekoff_date.append(first_date)
        public_holidays_date = self.get_public_holidays_dates(next_action_date, next_action_date1)
        for weekdate in weekoff_date:
            if weekdate not in public_holidays_date:
                final_weekoff.append(weekdate)
        return final_weekoff

    @api.model
    def _cron_generate_requests(self):
        """Generates maintenance request on the next_action_date or today if none exists"""
        for equipment in self.search([('period', '>', 0)]):
            next_requests = self.env['maintenance.request'].search([
                ('stage_id.done', '=', False),
                ('equipment_id', '=', equipment.id),
                ('maintenance_type', '=', 'preventive'),
                ('request_date', '=', equipment.next_action_date)])

            if not next_requests:
                public_holidays = self.get_public_holidays_dates(equipment.next_action_date, equipment.next_action_date) 
                weekoff_days = self.get_employee_weekoff(equipment.employee_id, equipment.next_action_date, equipment.next_action_date)
                total_days = public_holidays or weekoff_days
                    
                if equipment.next_action_date and equipment.period > 0:
                    equipment.next_action_date += timedelta(days=equipment.period)
                equipment._create_new_request(equipment.next_action_date)

    # @api.onchange('technician_user_id')
    # def onchange_technician_user_id(self):
    #     if self.technician_user_id:
    #         self.employee_id = self.technician_user_id.employee_id or self.env.user.employee_id or False

class MaintenanceStageInherit(models.Model):
    _inherit = 'maintenance.stage'

    stage_type = fields.Selection([
        ('new', 'New'),
        ('wait', 'Waiting For Approval'),
        ('approval', ' Approved'),
        ('in_progress', 'In Progress'),
        ('repaired', 'Repaired'),
        ('invoice', 'Invoiced'),
        ('scrap', 'Scrap')], string='Type')

class MaintenanceRequestInherit(models.Model):
    _inherit = 'maintenance.request'

    def _default_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    def _default_dest_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        lot_stock_id = self.env['stock.location'].search([('company_id', '=', company_id), ('usage', '=', 'inventory')], limit=1)
        if lot_stock_id:
            return lot_stock_id.id
        return None

    company_id = fields.Many2one('res.company')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    line_ids = fields.One2many('maintenance.request.line', 'request_id')
    location_id = fields.Many2one('stock.location', string='Source Location', domain="[('usage', '=', 'internal')]", default=_default_location_id)
    dest_location_id = fields.Many2one('stock.location', string='Destination Location', default=_default_dest_location_id)
    amount_total = fields.Monetary(string="Total", compute="_compute_amount_total",store=True)
    request_stage_type = fields.Selection(related='stage_id.stage_type', store=True)
    group_id = fields.Many2one('procurement.group')
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id", store=True)
    invoice_id = fields.Many2one('account.move')
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    checklist_ids = fields.Many2many('camp.asset.checklist.line')
    note = fields.Text(string="Note")
    description = fields.Text(string="Description")
    product_id = fields.Many2one('product.product',string="Product" )
    damage_ids = fields.One2many('camp.deduction.line','request_id')
    move_ids = fields.One2many('stock.move', 'request_id')
    invoice_ids = fields.One2many('account.move', 'request_id')
    task_ids = fields.One2many('project.task', 'maintenance_id')
    task_count = fields.Integer(compute='_compute_task_count')

    @api.onchange('equipment_id')
    def _onchange_equipment(self):
        if self.equipment_id:
            self.checklist_ids = [(6, 0, self.equipment_id.checklist_ids.ids)]
            self.product_id = self.equipment_id.product_id and self.equipment_id.product_id.id


    @api.onchange('equipment_id')
    def _compute_maintenance_team_id(self):
        res = super(MaintenanceRequestInherit, self)._compute_maintenance_team_id()
        self.employee_id = self.equipment_id.employee_id or self.env.user.employee_id or False
        return res

    def _compute_invoice_count(self):
        invoice_count = 0
        for rec in self:
            invoice_ids = self.env['account.move'].search([('request_id', '=', rec.id)])
            invoice_count = len(invoice_ids)
            rec.invoice_count = invoice_count

    @api.depends('line_ids.price_total')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('price_total'))

    def action_submit(self):
        stage_type_id = self.env['maintenance.stage'].search([('stage_type', '=', 'wait')], limit=1)
        if not stage_type_id:
            raise ValidationError(_('Please set type as (Wait) in maintenance stage.'))
        template_id = self.env.ref('pways_equipment_all_in_one.email_template_maintaince_request').id
        # template_id = self.env['ir.model.data']._xmlid_lookup('pways_equipment_all_in_one.email_template_maintaince_request')[2]
        if template_id:
            email_template_id = self.env['mail.template'].sudo().browse(template_id)
            email_template_id.send_mail(self.id)
            msg_body = _('Mail has been send to manager for maintaince request approval.')
            self.message_post(body=msg_body)
            self.stage_id = stage_type_id and stage_type_id.id

    def action_approval(self):
        stage_type_id = self.env['maintenance.stage'].search([('stage_type', '=', 'approval')], limit=1)
        if not stage_type_id:
            raise ValidationError(_('Please set type as (Approval) in maintenance stage.'))
        template_id = self.env.ref('pways_equipment_all_in_one.email_template_maintaince_allcoation_request').id
        if template_id:
            email_template_id = self.env['mail.template'].sudo().browse(template_id)
            email_template_id.send_mail(self.id)
            msg_body = _('Mail has been send to user that maintaince request is approved')
            self.message_post(body=msg_body)
            self.equipment_id.write({'equipment_status': 'maintenance'})
            self.stage_id = stage_type_id and stage_type_id.id

    def action_confim(self):
        if not self.line_ids:
            raise UserError(_("Please add items before process."))
        
        stage_type_id = self.env['maintenance.stage'].search([('stage_type', '=', 'in_progress')], limit=1)
        if not stage_type_id:
            raise ValidationError(_('Please set type as (In Progress) in maintenance stage.'))
        self.stage_id = stage_type_id.id

        if self.dest_location_id:
            location_dest_id = self.dest_location_id
        else:
            location_dest_id = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)

        warehouse_id = self.location_id.warehouse_id
        picking_type_id = warehouse_id.out_type_id
        group_id = self.env['procurement.group'].create({'name': self.name, 'request_id': self.id})
        self.write({'group_id': group_id.id})
        
        # check qty available
        line_ids = self.line_ids.filtered(lambda x: x.product_id.detailed_type != 'service')
        fil_line_ids = line_ids.filtered(lambda x: x.product_id.detailed_type == 'product')
        for fil_line in fil_line_ids:
            if fil_line.product_id.qty_available < fil_line.quantity:
                raise UserError(_('Product %s has only %s available qty') %(fil_line.product_id.name, fil_line.product_id.qty_available))
        # move
        move_list = []
        for line in line_ids:
            move_list.append((0,0,{
                'name': self.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': location_dest_id.id,
                'request_id': self.id,
                'origin': self.name,
                'company_id': self.company_id.id,
                'warehouse_id': warehouse_id.id,
                'group_id': group_id.id,
                'picking_type_id' : picking_type_id.id
            }))
        
        # picking
        picking = self.env['stock.picking'].create({
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id.id,
            'partner_id': self.user_id.partner_id.id,
            'picking_type_id' : picking_type_id.id,
            'move_ids_without_package': move_list,
        })
        if picking:
            picking.action_confirm()

        # project
        project = self.env['project.project'].search([('maintenance', '=', True)], limit=1)
        if not project:
           project =  self.env['project.project'].create({
                "name": 'Maintenance Project',
                'user_id': self.user_id.id,
                'maintenance_id': self.id,
                'partner_id': self.user_id.partner_id.id,
                'maintenance': True,
            })
        if project:
            self.env['project.task'].create({
                "name": "%s-%s" %('Maintenance JOB', self.product_id.name),
                'user_ids': [(4, self.user_id.id)],
                'project_id': project.id,
                'maintenance_id': self.id,
                'partner_id': self.user_id.partner_id.id,
            })
        return True

    def archive_equipment_request(self):
        if self.move_ids and self.move_ids.mapped('state') not in ['done', 'cancel']:
            for move in self.move_ids:
                move._action_cancel()
        return super(MaintenanceRequestInherit, self).archive_equipment_request()

    def action_in_progress(self):
        stage_type_id = self.env['maintenance.stage'].search([('stage_type', '=', 'repaired')], limit=1)
        if not stage_type_id:
            raise ValidationError(_('Please set type as (Repaired) in maintenance stage.'))

        for move in self.move_ids.filtered(lambda x: x.state == 'assigned' and x.product_uom_qty == x.availability):
            move.write({'quantity': move.availability})
            # move.write({'quantity_done': move.availability})
            move._action_done()
        # for move in self.move_ids.filtered(lambda x: x.state == 'assigned' and x.product_uom_qty == x.reserved_availability):
        #     move.write({'quantity_done': move.reserved_availability})
        #     move._action_done()

        if all([move.state == 'done' for move in self.move_ids]):
            self.stage_id = stage_type_id.id

        return True

    def action_request_moves(self):
        move_ids = self.env['stock.move'].search([('request_id', '=', self.id)])
        return {
            'name': _('Pickings'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids.mapped('picking_id').ids)],
        }

    def open_invoices(self):
        invoice_ids = self.env['account.move'].search([('request_id', '=', self.id)])
        return {
            'name': _('Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoice_ids.ids)],
        }

    def _prepare_invoice_line(self, line):
        res = {
            'name': line.product_id.name,
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom_id.id,
            'quantity': line.quantity,
            'price_unit': line.price_unit,
            'tax_ids': [(6, 0, line.tax_ids.ids)],
        }
        return res

    
    def _compute_task_count(self):
        task_count = 0
        for rec in self:
            task_ids = self.env['project.task'].search([('maintenance_id', '=', rec.id)])
            task_count = len(task_ids)
            rec.task_count = task_count

    def open_task(self):
        task_ids = self.env['project.task'].search([('maintenance_id', '=', self.id)])
        return {
            'name': _('Job Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', task_ids.ids)],
        }

    def action_create_invoice(self):
        invoice_id = self.env['account.move']
        journal = self.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', self.company_id.id)])
        for rec in self.filtered(lambda x: not x.invoice_id):
            invoice_line_vals = []
            company_id = rec.company_id
            if not journal:
                raise UserError(_('Please define an accounting purchase journal for the company %s (%s).', company_id.name, company_id.id))
            stage_type_id = self.env['maintenance.stage'].search([('stage_type', '=', 'invoice')], limit=1)
            if not stage_type_id:
                raise ValidationError(_('Please set type as (Invoiced) in maintenance stage.'))
            for line in rec.line_ids:
                invoice_line_vals.append((0, 0, self._prepare_invoice_line(line)))
            if invoice_line_vals:
                invoice_vals = {
                    'ref': company_id.partner_id.name or '',
                    'move_type': 'in_invoice',
                    'narration': rec.description,
                    'currency_id': company_id.currency_id.id,
                    'user_id': rec.user_id.id or self.env.user.id,
                    'invoice_user_id': rec.user_id.id or self.env.user.id,
                    'partner_id': company_id.partner_id.id,
                    'journal_id': journal.id,
                    'invoice_origin': "%s" %(rec.name),
                    'payment_reference': rec.name,
                    'invoice_line_ids': invoice_line_vals,
                    'company_id': company_id.id,
                    'invoice_date': fields.Date.today(),
                    'request_id': self.id,
                }
                invoice_id = self.env['account.move'].create(invoice_vals)
                rec.stage_id = stage_type_id.id
        self.equipment_id.write({'equipment_status': 'occupy'})
        return True

class MaintenanceRequestLine(models.Model):
    _name = 'maintenance.request.line'
    _description = 'Maintenance Request Line'

    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float('Quantity', default=1.0, digits='Product Unit of Measure')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True, domain="[('category_id', '=', product_uom_category_id)]",)
    request_id = fields.Many2one('maintenance.request', string="Maintenance Request", ondelete='cascade')
    price_unit = fields.Float(string='Unit Price')
    currency_id = fields.Many2one('res.currency', related="request_id.currency_id", store=True)
    tax_ids = fields.Many2many('account.tax')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price or 0.0
            self.product_uom_id = self.product_id.uom_id and self.product_id.uom_id.id or False

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.tax_ids.compute_all(price, line.currency_id, line.quantity, product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
