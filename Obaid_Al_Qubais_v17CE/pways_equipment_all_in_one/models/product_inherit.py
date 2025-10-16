
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def defualt_maintenance(self):
        team_id = self.env['maintenance.team'].search([], limit=1)
        return team_id and team_id.id

    def defualt_maintenance_category(self):
        team_id = self.env['maintenance.equipment.category'].search([], limit=1)
        return team_id and team_id.id

    def defualt_technician(self):
        team_id = self.env['res.users'].search([], limit=1)
        return team_id and team_id.id

    equipment = fields.Boolean(string='Can be Equipment')
    maintenance_id = fields.Many2one('maintenance.team' ,string='Maintenance Team', default=defualt_maintenance)
    category_id = fields.Many2one('maintenance.equipment.category' ,string="Category", default=defualt_maintenance_category)
    technician_id =fields.Many2one('res.users', string="Technician", default=defualt_technician)
    equipment_assign_to = fields.Selection([('department', 'Department'), ('employee', 'Employee'), ('other', 'Other')],
        string='Used By',
        default='employee')
    equipment_created = fields.Boolean(copy=False)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     templates = super(ProductTemplate, self).create(vals_list)
    #     for temp in templates.filtered(lambda x: x.equipment and x.tracking == 'none'):
    #         equipment = self.env['maintenance.equipment'].create({
    #             "name": temp.name,
    #             'category_id': temp.category_id.id,
    #             'maintenance_team_id': temp.maintenance_id.id,
    #             'technician_user_id': temp.technician_id.id,
    #             'product_id': temp.product_variant_id.id,
    #             'equipment_assign_to': temp.equipment_assign_to,
    #             'cost': temp.standard_price,
    #         })
    #         temp.equipment_created = True
    #     return templates

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def defualt_maintenance(self):
        team_id = self.env['maintenance.team'].search([], limit=1)
        return team_id and team_id.id

    def defualt_maintenance_category(self):
        team_id = self.env['maintenance.equipment.category'].search([], limit=1)
        return team_id and team_id.id

    def defualt_technician(self):
        team_id = self.env.user
        return team_id and team_id.id

    equipment = fields.Boolean(string='Can be Equipment')
    maintenance_id = fields.Many2one('maintenance.team' ,string='Maintenance Team', default=defualt_maintenance)
    category_id = fields.Many2one('maintenance.equipment.category' ,string="Category", default=defualt_maintenance_category)
    technician_id =fields.Many2one('res.users', string="Technician", default=defualt_technician)
    equipment_assign_to = fields.Selection([('department', 'Department'), ('employee', 'Employee'), ('other', 'Other')],
        string='Used By',default='employee')
    equipment_created = fields.Boolean(copy=False)

class Picking(models.Model):
    _inherit = "stock.picking"

    allocation_id = fields.Many2one('allcation.request')

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    equipment_location_id = fields.Many2one('stock.location', string='Equipment Location')

class ProjectTask(models.Model):
    _inherit = "project.task"

    maintenance_id = fields.Many2one('maintenance.request',string='Maintenance')

class ProjectTask(models.Model):
    _inherit = "project.project"

    maintenance_id = fields.Many2one('maintenance.request' ,string='Maintenance')
    maintenance = fields.Boolean(copy=False)


class StockLot(models.Model):
    _inherit = 'stock.lot'

    @api.model_create_multi
    def create(self, vals_list):
        lots = super(StockLot, self).create(vals_list)
        for lot in lots:
            if lot.product_id.tracking == 'serial' and lot.product_id.equipment:
                equipment = self.env['maintenance.equipment'].create({
                    "name": lot.product_id.name,
                    'category_id': lot.product_id.category_id.id,
                    'maintenance_team_id': lot.product_id.maintenance_id.id,
                    'technician_user_id': lot.product_id.technician_id.id,
                    'product_id': lot.product_id.product_variant_id.id,
                    'equipment_assign_to': lot.product_id.equipment_assign_to,
                    'cost': lot.product_id.standard_price,
                    'serial_no': lot.name,
                    'serial_id': lot.id,
                })
                lot.product_id.equipment_created = True
        return lots


