from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging
import base64
import qrcode
from io import BytesIO
from datetime import date, timedelta

_logger = logging.getLogger(__name__)


class AssetTagMaster(models.Model):
    _name = 'asset.tag.master'
    _description = 'Asset Tag Master'

    name = fields.Char(string='Asset Tag', required=True)
    lot_ref_id = fields.Many2one('stock.lot', string='Lot/Serial')
    product_id = fields.Many2one('product.template', string='Product')
    valid_lot_ids = fields.Many2many('stock.lot', compute='_compute_valid_lot_ids', store=False)
    # part_number = fields.Char(string='Part Number')
    available_lot_ids = fields.Many2many('stock.lot', compute='_compute_available_lots')


    _sql_constraints = [
        ('unique_asset_tag_name', 'unique(name)', 'Asset Tag must be unique.')
    ]

    @api.onchange('lot_ref_id')
    def _onchange_lot_ref_id(self):
        if self.lot_ref_id:
            is_scrapped = self.env['stock.scrap'].search_count([
                ('lot_id', '=', self.lot_ref_id.id)
            ]) > 0

            if is_scrapped:
                warning = {
                    'title': 'Invalid Lot Selected',
                    'message': f"The selected lot '{self.lot_ref_id.name}' has been scrapped and cannot be used.",
                }
                self.lot_ref_id = False
                return {'warning': warning}

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    name = fields.Char('Asset Name', required=True, translate=True)
    seq_number = fields.Char('Sequence Number', required=True, copy=False, readonly=True, default='New')
    category_id = fields.Many2one(
        'account.asset.category',
        string='Asset Category',
        tracking=True,
        group_expand='_read_group_category_ids',
        ondelete='set null'
    )
    project_id = fields.Many2one('project.project', string='Project Assigned')
    item_code = fields.Char('Item No.')
    item_name = fields.Char('Item Description')
    frgn_name = fields.Char('Foreign Name')
    dflt_wh = fields.Many2one('stock.warehouse', string='Default Warehouse')
    exit_wh = fields.Many2one('stock.warehouse', string='Release Warehouse')
    picture_name = fields.Char('Picture')
    proj_code = fields.Char('Project Code')
    proj_name = fields.Char('Project Name')
    location = fields.Char('Location')
    stock_location = fields.Char('Stock Location')
    sub_category = fields.Char('Subcategory')
    item_notes = fields.Text('Item Notes')
    supplier_contact = fields.Char('Supplier Contact')
    payment_terms = fields.Char('Payment Terms')
    delivery_terms = fields.Char('Delivery Terms')
    stock_movement = fields.Char('Stock Movement')
    location_code = fields.Char('Location Code')
    serial_no = fields.Char('Serial Number of the Asset')
    maintenance_schedule = fields.Char('Maintenance Schedule')
    condition = fields.Selection([
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ], string='Condition')
    inspection_status = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], string='Inspection Status')
    asset_tag_id = fields.Many2one('asset.tag.master', string='Asset Tag')
    asset_type = fields.Char('Asset Type')
    asset_lifecycle_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('scrap', 'Scrap'),
        ('disposed', 'Disposed'),
        ('maintenance', 'Maintenance'),
    ], string='Asset Lifecycle Status')
    disposal_method = fields.Char('Disposal Method')
    equipment_type = fields.Char('Equipment Type')
    u_cn = fields.Char('Chassis No')
    u_vptlno = fields.Char('Vehicle Plate No')
    u_ml = fields.Char('Model')
    u_cln = fields.Char('Client Name')
    u_bs = fields.Char('Business Segment')
    u_bsc = fields.Char('Business Segment Code')
    u_crdcode = fields.Char('Client Code')
    job_title = fields.Char('Job Title')
    position = fields.Char('Position')
    room_id = fields.Many2one('camp.room', string="Assigned Room")
    value = fields.Float(string="Asset Value", help="Monetary value of the equipment")
    shared_with_ids = fields.Many2many('hr.employee', string="Shared With")
    accounting_asset_id = fields.Many2one(
        'account.asset.asset',
        string='Accounting Asset',
        domain="[('linked_equipment_id', '=', False)]",
    )
    qr_code = fields.Binary("QR Code")
    qr_proccessed = fields.Boolean("QR Code")

    total_quantity = fields.Integer(string="Total Quantity", default=1)
    allocated_quantity = fields.Integer(string="Allocated", compute="_compute_allocated_quantities", store=True)
    damaged_quantity = fields.Integer(string="Damaged", default=0)
    missing_quantity = fields.Integer(string="Missing", default=0)
    available_quantity = fields.Integer(string="Available", compute="_compute_available_quantity", store=True)

    camp_allocation_line_ids = fields.One2many('camp.asset.checklist.line', 'asset_id', string="Allocations")
    sap_fa_code = fields.Char(string="SAP FA-Code")
    employee_id = fields.Many2one('hr.employee', string='Assigned Employee', readonly =True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('scrap', 'Scraped'),
        ('damaged', 'Damaged'),
        ('missing', 'Missing'),
    ], string='Status', default='draft', tracking=True)
    product_id = fields.Many2one('product.product', string='Product')
    unit_ids = fields.One2many('equipment.unit.line', 'equipment_id', string="Units")
    assigned_assets_in_room = fields.Many2many(
        'maintenance.equipment',
        compute='_compute_assigned_assets_in_room',
        string="Assets in Room"
    )
    employee_barcode = fields.Char(
        string="Employee ID",
        related='employee_id.barcode',
        store=True,
        readonly=True
    )
    product_cost = fields.Float(string='Asset Cost')
    is_expensive = fields.Boolean(string='Is Expensive?', readonly=True)
    _sql_constraints = [
        ('unique_asset_tag', 'unique(asset_tag_id)', 'Please Check The Asset Tag!'),
    ]
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial')
    sync_lot_to_tag = fields.Boolean(
        compute="_compute_sync_lot_to_tag",
        store=False
    )
    #CODE
    asset_tag_readonly = fields.Boolean(string="Asset Tag Readonly", compute="_compute_asset_tag_readonly")
    external_contact_id = fields.Many2one('res.partner', string='External Company')

    @api.depends('accounting_asset_id.asset_tag_id')
    def _compute_asset_tag_readonly(self):
        for record in self:
            record.asset_tag_readonly = bool(record.accounting_asset_id.asset_tag_id)


    @api.depends('lot_id', 'asset_tag_id')
    def _compute_sync_lot_to_tag(self):
        for rec in self:
            if rec.lot_id and rec.asset_tag_id and rec.asset_tag_id.lot_ref_id != rec.lot_id:
                rec.asset_tag_id.lot_ref_id = rec.lot_id
            rec.sync_lot_to_tag = True

    @api.onchange('category_id')
    def _onchange_category_id_set_expensive(self):
        """
        Set is_expensive when category changes, but only in draft state.
        """
        for record in self:
            if record.state == 'draft' and record.category_id:
                record.is_expensive = record.category_id.is_expensive

    @api.onchange('product_id')
    def _onchange_product_id_set_tag(self):
        if self.product_id:
            lot = self.env['stock.lot'].search([('product_id', '=', self.product_id.id)], limit=1)
            self.serial_no = False
            if self.asset_tag_id:
                self.asset_tag_id.lot_ref_id = lot.id if lot else False
                # self.asset_tag_id.part_number = self.product_id.default_code

    @api.model
    def create(self, vals):
        equipment = super().create(vals)
        if equipment.product_id and equipment.asset_tag_id:
            lot = self.env['stock.lot'].search([('product_id', '=', equipment.product_id.id)], limit=1)
            if lot:
                equipment.serial_no = lot.name
                equipment.asset_tag_id.serial_number = lot.name
                # equipment.asset_tag_id.part_number = equipment.product_id.default_code
        return equipment

    @api.onchange('asset_tag_id')
    def _onchange_asset_tag_id(self):
        for rec in self:
            if rec.asset_tag_id:
                if rec.asset_tag_id.lot_ref_id:
                    rec.lot_id = rec.asset_tag_id.lot_ref_id.id
                else:
                    rec.asset_tag_id.lot_ref_id = rec.lot_id

    @api.constrains('asset_tag_id')
    def _check_asset_tag_no_spaces(self):
        for record in self:
            # existing = self.search([('asset_tag', '=', record.asset_tag), ('id', '!=', record.id)], limit=1)
            # if existing:
            #     raise ValidationError("The Asset Tag must be unique!")
            if record.asset_tag_id:
                if ' ' in record.asset_tag_id:
                    raise ValidationError("The Asset Tag must not contain spaces. Please correct the value.")

    def _default_warranty(self):
        today = date.today()
        start = today.strftime("%d/%m/%y")
        end = (today + timedelta(days=365)).strftime("%d/%m/%y")
        serial = "1234"
        return f"{start}/{serial}/{end}"

    warranty = fields.Char(
        string='Warranty',
        default=_default_warranty,
        help="Format: DD/MM/YY/SERIAL/DD/MM/YY"
    )
    # _sql_constraints = [
    #     ('unique_employee_barcode', 'unique(employee_barcode)', 'The employee barcode must be unique!')
    # ]


    @api.onchange('category_id')
    def _onchange_category_expensive(self):
        self.employee_id = None
        if self.category_id:
            self.is_expensive = self.category_id.is_expensive


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            domain = ['|', '|',
                      ('name', operator, name),
                      ('asset_tag_id', operator, name),
                      ('employee_barcode', operator, name)]
            args = domain + args
        return super(MaintenanceEquipment, self).name_search(name=name, args=args, operator=operator, limit=limit)

    def open_scrap_wizard(self):
        self.ensure_one()
        if self.project_id or self.employee_id or self.room_id:
            raise ValidationError("You cannot scrap the Allocated Assets.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Scrap Asset',
            'res_model': 'asset.scrap.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_asset_id': self.id,
            }
        }

    @api.depends('unit_ids.allocated')
    def _compute_allocated_quantities(self):
        for rec in self:
            rec.allocated_quantity = len(rec.unit_ids.filtered(lambda u: u.allocated))
            rec.available_quantity = rec.total_quantity - rec.allocated_quantity

    @api.depends('total_quantity', 'allocated_quantity')
    def _compute_available_quantity(self):
        for record in self:
            record.available_quantity = record.total_quantity - record.allocated_quantity

    @api.depends('total_quantity', 'allocated_quantity', 'damaged_quantity', 'missing_quantity')
    def _compute_available_quantity(self):
        for record in self:
            record.available_quantity = (
                record.total_quantity - record.allocated_quantity - record.damaged_quantity - record.missing_quantity
            )

    @api.depends('camp_allocation_line_ids')
    def _compute_allocated_quantity(self):
        for record in self:
            record.allocated_quantity = len(record.camp_allocation_line_ids)

    @api.model
    def create(self, vals):
        name_from_form = vals.get('name')
        if vals.get('seq_number', 'New') == 'New':
            vals['seq_number'] = self.env['ir.sequence'].next_by_code('maintenance.equipment.seq') or _('New')

        record = super().create(vals)

        if name_from_form:
            record.name = name_from_form

        if record.asset_tag_id and record.lot_id:
            record.asset_tag_id.lot_ref_id = record.lot_id.id
        return record

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.asset_tag_id and rec.lot_id:
                rec.asset_tag_id.lot_ref_id = rec.lot_id.id
        return res

    def action_generate_qr_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.qr_proccessed:
                raise UserError("QR code has already been generated for this asset.")

            if not record.sap_fa_code:
                raise UserError("SAP FA-Code is mandatory to generate QR code.")

            equipment_url = f"{base_url}/web#id={record.id}&model=maintenance.equipment&view_type=form"

            qr_text = (
                f"Asset Number: {record.seq_number}\n"
                f"SAP FA-Code: {record.sap_fa_code}\n"
                f"Assigned To: {record.employee_id.name or 'N/A'}\n"
                f"Location: {record.location or 'N/A'}\n"
                f"Project: {record.project_id.name or 'N/A'}\n"
                f"URL: {equipment_url}"
            )

            qr = qrcode.QRCode(box_size=3, border=2)
            qr.add_data(qr_text)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_image = base64.b64encode(buffer.getvalue())
            record.qr_code = qr_image
            record.qr_proccessed = True
            record.state = 'validated'

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            name = record.name or ''
            serial = record.serial_no or ''
            record.display_name = f"{name}/{serial}" if serial else name


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    linked_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Linked Equipment',
        ondelete='set null',
        readonly=True,
        copy=False,
    )
    product_id = fields.Many2one('product.product', string='Product')
    asset_tag_id = fields.Many2one('asset.tag.master', store=True, string='Asset Tag')
    warranty = fields.Char(string='Warranty')
    lot_id = fields.Many2one('stock.lot', string='Serial Number')

    @api.onchange('asset_tag_id')
    def _onchange_asset_tag_id(self):
        for rec in self:
            if rec.asset_tag_id and rec.lot_id:
                rec.asset_tag_id.lot_ref_id = rec.lot_id

    @api.model
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        assets = super().create(vals_list)

        used_lot_ids = self.search([('lot_id', '!=', False)]).mapped('lot_id').ids
        product_ids = set(asset.product_id.id for asset in assets if asset.product_id)

        move_lines = self.env['account.move.line'].search([
            ('product_id', 'in', list(product_ids)),
            ('purchase_line_id', '!=', False),
        ])

        po_ids = move_lines.mapped('purchase_line_id.order_id').ids
        pickings = self.env['stock.picking'].search([
            ('purchase_id', 'in', po_ids),
            ('state', '=', 'done')
        ])

        lot_map_by_product = {}
        for picking in pickings:
            for sm_line in picking.move_line_ids:
                if sm_line.lot_id and sm_line.lot_id.id not in used_lot_ids:
                    lot_map_by_product.setdefault(sm_line.product_id.id, []).append(sm_line.lot_id)

        lot_pointer = {}
        for asset in assets:
            if not asset.lot_id and asset.product_id:
                product_id = asset.product_id.id
                available_lots = lot_map_by_product.get(product_id, [])
                if not available_lots:
                    raise UserError(f"No available receipt lot found for product {asset.product_id.display_name}")

                if product_id not in lot_pointer:
                    lot_pointer[product_id] = 0
                index = lot_pointer[product_id]

                if index >= len(available_lots):
                    raise UserError(f"Not enough unique lots available for product {asset.product_id.display_name}")

                assigned_lot = available_lots[index]
                asset.lot_id = assigned_lot.id
                lot_pointer[product_id] += 1

                if asset.asset_tag_id:
                    asset.asset_tag_id.lot_ref_id = assigned_lot.id

        for asset in assets:
            if not asset.linked_equipment_id:
                move_line = self.env['account.move.line'].search(
                    [('asset_category_id', '=', asset.id)], limit=1)
                purchase_qty = int(
                    move_line.purchase_line_id.product_qty) if move_line and move_line.purchase_line_id else 1

                equipment_vals = {
                    'name': asset.name or 'Unnamed',
                    'seq_number': self.env['ir.sequence'].next_by_code('maintenance.equipment.seq') or 'New',
                    'category_id': asset.category_id.id,
                    'accounting_asset_id': asset.id,
                    'value': asset.value,
                    'product_id': asset.product_id.id,
                    'company_id': asset.company_id.id if asset.company_id else self.env.company.id,
                    'sap_fa_code': asset.code,
                    'total_quantity': purchase_qty,
                    'asset_tag_id': asset.asset_tag_id.id,
                    'product_cost': asset.value_residual,
                    'warranty': asset.warranty,
                    'lot_id': asset.lot_id.id,
                    'is_expensive': asset.category_id.is_expensive,
                }

                equipment = self.env['maintenance.equipment'].create(equipment_vals)
                asset.write({'linked_equipment_id': equipment.id})

                for i in range(purchase_qty):
                    self.env['equipment.unit.line'].create({
                        'equipment_id': equipment.id,
                        'unit_name': f"{asset.name or 'Unit'} #{i + 1}",
                        'asset_tag_id': asset.asset_tag_id.id,
                    })

        return assets if len(assets) > 1 else assets[0]

    def write(self, vals):
        res = super().write(vals)
        for asset in self:
            if asset.linked_equipment_id:
                if vals.get('asset_tag_id'):
                    asset.linked_equipment_id.asset_tag_id = vals['asset_tag_id']
                if vals.get('name'):
                    asset.linked_equipment_id.name = vals['name']
        return res


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    parent_category = fields.Many2one(
        'maintenance.equipment.category',
        string="Parent Category",
        index=True,
        ondelete='cascade',
    )
    is_expensive = fields.Boolean("Is Expensive?")
    asset_category_id = fields.Many2one(
        'account.asset.category',
        string='Accounting Asset Category',
        help="Used for automatic asset creation."
    )

    complete_name = fields.Char(
        string="Full Category Name",
        compute='_compute_complete_name',
        store=True,
        recursive=True
    )
    _parent_name = 'parent_category'
    _parent_store = True
    parent_path = fields.Char(index=True)
    _rec_name = 'complete_name'
    _order = 'complete_name'

    @api.depends('name', 'parent_category.complete_name')
    def _compute_complete_name(self):
        for rec in self:
            if rec.parent_category:
                rec.complete_name = f"{rec.parent_category.complete_name} / {rec.name}"
            else:
                rec.complete_name = rec.name

    def unlink(self):
        for category in self:
            if self.env['maintenance.equipment'].search_count([
                ('category_id', '=', category.id)
            ]):
                raise UserError(_("Cannot delete category '%s' as it's linked to equipment.") % category.name)
        return super().unlink()


class EquipmentUnitLine(models.Model):
    _name = 'equipment.unit.line'
    _description = 'Unit Allocation Line'

    equipment_id = fields.Many2one('maintenance.equipment', string="Asset", ondelete='cascade')
    unit_name = fields.Char(string="Unit Name")
    asset_tag_id = fields.Many2one('asset.tag.master', related='equipment_id.asset_tag_id', store=True, string='Asset Tag')
    price_unit = fields.Float(related='equipment_id.product_cost')
    serial_no = fields.Char(string="Serial Number")
    allocated = fields.Boolean(string="Allocated")
    allocation_line_id = fields.Many2one('asset.allocation.line', string="Allocation Ref")
    condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used'),
        ('damaged', 'Damaged'),
    ], string="Condition")
    lot_id = fields.Many2one('stock.lot', string="Serial/Lot Number")


class CampAssetChecklistLine(models.Model):
    _inherit = 'camp.asset.checklist.line'

    allocated_unit_ids = fields.Many2many('maintenance.equipment.unit', string="Allocated Units")

    @api.model
    def create(self, vals):
        line = super().create(vals)
        if 'allocated_unit_ids' in vals:
            for unit_id in vals['allocated_unit_ids'][0][2]:
                unit = self.env['maintenance.equipment.unit'].browse(unit_id)
                unit.write({'allocated': True, 'allocation_line_id': line.id})
        return line

    def unlink(self):
        for line in self:
            for unit in line.allocated_unit_ids:
                unit.write({'allocated': False, 'allocation_line_id': False})
        return super().unlink()
