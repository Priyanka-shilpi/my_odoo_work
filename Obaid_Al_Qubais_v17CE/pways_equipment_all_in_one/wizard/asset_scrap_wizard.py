from odoo import models, fields, _
from odoo.exceptions import UserError


class AssetScrapWizard(models.TransientModel):
    _name = 'asset.scrap.wizard'
    _description = 'Scrap Equipment Wizard'

    asset_id = fields.Many2one('maintenance.equipment', required=True, string='Asset')
    reason = fields.Selection([
        ('physically_damaged', 'Physically Damaged'),
        ('irreparable', 'Irreparable'),
        ('lost', 'Lost'),
        ('other', 'Other'),
    ], required=True, string="Reason")
    reason_note = fields.Text('Reason Details')

    def action_scrap(self):
        self.ensure_one()
        asset = self.asset_id

        if asset.asset_lifecycle_status == 'scrap':
            raise UserError(_("This asset is already marked as Scrapped."))

        allocation_active = self.env['asset.allocation.request'].search_count([
            ('asset_id', '=', asset.id),
            ('state', '=', 'allocated')
        ]) > 0
        assigned_to_room = bool(asset.room_id)

        if allocation_active or assigned_to_room:
            raise UserError(_("This asset is currently allocated either to an employee/project or assigned to a room. "
                              "Please remove the allocation or room assignment before marking it as scrapped."))

        lot = asset.asset_tag_id.lot_ref_id
        if not lot:
            raise UserError(_("No serial/lot number linked to this asset tag."))

        # Optional: stock availability check
        # quant = self.env['stock.quant'].search([
        #     ('lot_id', '=', lot.id),
        #     ('product_id', '=', asset.product_id.id),
        #     ('quantity', '>', 0)
        # ], limit=1)
        # if not quant:
        #     raise UserError(_("No available stock for this asset's lot."))

        scrap = self.env['stock.scrap'].create({
            'product_id': asset.product_id.id,
            'product_uom_id': asset.product_id.uom_id.id,
            'scrap_qty': 1,
            'lot_id': lot.id,
            'location_id': lot.location_id.id,
            'origin': f"Asset Scrap - {asset.name}",
            'asset_tag_id': asset.asset_tag_id.id,
        })
        scrap.action_validate()

        reason_label = dict(self._fields['reason'].selection).get(self.reason)
        full_reason = f"{reason_label}: {self.reason_note or ''}"

        asset.write({
            'asset_lifecycle_status': 'scrap',
            'state': 'scrap',
        })
        asset.message_post(
            body=_(
                f"Asset marked as Scrapped by {self.env.user.name} on {fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
                f"Reason: {full_reason}"
            ),
            message_type='comment'
        )

        if lot:
            lot.message_post(body=f"Lot scrapped via asset: {asset.name}")
            lot.is_scrapped = True

        if asset.product_id and asset.product_id.qty_available <= 0:
            asset.product_id.message_post(body=f"Product archived after asset {asset.name} was scrapped.")

        # Link to accounting asset and dispose it
        accounting_asset = self.env['account.asset.asset'].search([('linked_equipment_id', '=', asset.id)], limit=1)
        if accounting_asset:
            return accounting_asset.set_to_close()  # This will return the journal entry action
        else:
            raise UserError(_("This asset is not linked to any Accounting Asset. Cannot finalize disposal."))


class StockLot(models.Model):
    _inherit = 'stock.lot'

    is_scrapped = fields.Boolean("Is Scrapped", default=False)
