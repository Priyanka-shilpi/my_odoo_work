from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging


_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    batch_id = fields.Many2one(
        'stock.picking.batch', string='Batch Transfer',
        check_company=True,
        help='Batch associated to this transfer', index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking, vals in zip(pickings, vals_list):
            if vals.get('batch_id'):
                if not picking.batch_id.picking_type_id:
                    picking.batch_id.picking_type_id = picking.picking_type_id[0]
                picking.batch_id._sanity_check()
        return pickings

    def write(self, vals):
        old_batches = self.batch_id
        res = super().write(vals)
        if vals.get('batch_id'):
            old_batches.filtered(lambda b: not b.picking_ids).state = 'cancel'
            if not self.batch_id.picking_type_id:
                self.batch_id.picking_type_id = self.picking_type_id[0]
            self.batch_id._sanity_check()
            self.batch_id.picking_ids.assign_batch_user(self.batch_id.user_id.id)
        return res

    def action_add_operations(self):
        view = self.env.ref('stock_picking_batch.view_move_line_tree_detailed_wave')
        return {
            'name': _('Add Operations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'view': view,
            'views': [(view.id, 'tree')],
            'res_model': 'stock.move.line',
            'target': 'new',
            'domain': [
                ('picking_id', 'in', self.ids),
                ('state', '!=', 'done')
            ],
            'context': dict(
                self.env.context,
                picking_to_wave=self.ids,
                active_wave_id=self.env.context.get('active_wave_id').id,
                search_default_by_location=True,
            )}

    def action_confirm(self):
        res = super().action_confirm()
        for picking in self:
            if hasattr(picking, '_find_auto_batch'):
                picking._find_auto_batch()
        return res

    def button_validate(self):
        res = super().button_validate()
        to_assign_ids = set()
        if not any(picking.state == 'done' for picking in self):
            return res
        if self and self.env.context.get('pickings_to_detach'):
            pickings_to_detach = self.env['stock.picking'].browse(self.env.context['pickings_to_detach'])
            pickings_to_detach.batch_id = False
            pickings_to_detach.move_ids.filtered(lambda m: not m.quantity).picked = False
            to_assign_ids.update(self.env.context['pickings_to_detach'])

        for picking in self:
            if picking.state != 'done':
                continue
            if picking.batch_id and any(p.state != 'done' for p in picking.batch_id.picking_ids):
                picking.batch_id = None
            to_assign_ids.update(picking.backorder_ids.ids)

        assignable_pickings = self.env['stock.picking'].browse(to_assign_ids)
        for picking in assignable_pickings:
            if hasattr(picking, '_find_auto_batch'):
                picking._find_auto_batch()

        return res

    def action_transfer_from_asset(self, asset):
        if not asset.asset_tag_id or not asset.asset_tag_id.lot_ref_id:
            raise UserError("Please assign an asset tag with a valid serial number.")

        if not asset.product_id:
            raise UserError("Asset must have a product.")

        lot = asset.asset_tag_id.lot_ref_id

        quant = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('product_id', '=', asset.product_id.id),
            ('quantity', '>', 0)
        ], limit=1)

        if not quant:
            raise UserError("No available stock found for this lot.")

        po_line = asset.purchase_line_id if hasattr(asset, 'purchase_line_id') else False
        if po_line and po_line.order_id.invoice_status != 'invoiced':
            raise UserError("Cannot transfer asset until the purchase bill is confirmed.")


        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'location_id': quant.location_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'origin': f"Transfer from Asset: {asset.name}",
        })

        move = self.env['stock.move'].create({
            'name': asset.name,
            'picking_id': picking.id,
            'product_id': asset.product_id.id,
            'product_uom_qty': 1,
            'product_uom': asset.product_id.uom_id.id,
            'location_id': quant.location_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
        })

        picking.action_confirm()
        picking.action_assign()

        move.move_line_ids.unlink()

        self.env['stock.move.line'].create({
            'move_id': move.id,
            'picking_id': picking.id,
            'product_id': asset.product_id.id,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
            'product_uom_id': asset.product_id.uom_id.id,
            'qty_done': 1,
            'lot_id': lot.id,
            'lot_name': lot.name,
        })

        move.lot_ids = [(6, 0, [lot.id])]

        picking.button_validate()
        return picking


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'


    asset_tag_id = fields.Many2one(
        'asset.tag.master',
        string='Asset Tag',
        compute='_compute_asset_tag_id',
        store=False,
        readonly=False,
    )

    @api.depends('lot_id')
    def _compute_asset_tag_id(self):
        for line in self:
            tag = False
            if line.lot_id:
                tag = self.env['asset.tag.master'].search([
                    ('lot_ref_id', '=', line.lot_id.id)
                ], limit=1)
            line.asset_tag_id = tag

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for line in self:
            if line.lot_id:
                tag = self.env['asset.tag.master'].search([
                    ('lot_ref_id', '=', line.lot_id.id)
                ], limit=1)
                if tag:
                    line.asset_tag_id = tag

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_create_invoice(self):
        for order in self:
            for line in order.order_line:
                product = line.product_id
                if not product:
                    continue

                scrapped_lots = self.env['stock.lot'].search([
                    ('product_id', '=', product.id),
                    ('is_scrapped', '=', True)
                ])
                if scrapped_lots:
                    lot_names = ', '.join(scrapped_lots.mapped('name'))
                    order.message_post(body=_(
                        f"The product '{product.display_name}' has scrapped lot(s): {lot_names}. "
                        f"Please ensure you select only available serials during invoice creation."
                    ))

                location_moves = self.env['stock.move'].search([
                    ('product_id', '=', product.id),
                    ('state', '=', 'done'),
                    ('location_dest_id.usage', 'in', ['inventory', 'transit', 'customer']),
                ], limit=1)

                if location_moves:
                    order.message_post(body=_(
                        f"Product '{product.display_name}' is already moved to location: {location_moves.location_dest_id.display_name}."
                    ))

        return super().action_create_invoice()

