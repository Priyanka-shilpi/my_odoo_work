from odoo import models, fields, tools

class FuelReport(models.Model):
    _name = 'fuel.report'
    _description = 'Monthly Fuel Report'
    _auto = False

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', readonly=True)
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
        ('lpg', 'LPG'),
        ('lng', 'LNG'),
        ('biodiesel', 'Biodiesel'),
        ('ethanol', 'Ethanol'),
        ('hydrogen', 'Hydrogen'),
        ('methanol', 'Methanol'),
    ], string='Fuel Type', readonly=True)

    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    total_fuel = fields.Float(string='Total Fuel (Liters)', readonly=True)
    month = fields.Char(string='Month', readonly=True)

    def init(self):
        self.env.cr.execute("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'fuel_report' AND relkind = 'r') THEN
                    EXECUTE 'DROP TABLE fuel_report CASCADE';
                ELSIF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'fuel_report' AND relkind = 'v') THEN
                    EXECUTE 'DROP VIEW fuel_report CASCADE';
                END IF;
            END
            $$;
        """)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW fuel_report AS (
                SELECT
                    MIN(fe.id) AS id,
                    fe.vehicle_id,
                    fe.fuel_type,
                    emp.department_id,
                    SUM(fe.quantity) AS total_fuel,
                    TO_CHAR(fe.date, 'Month YYYY') AS month
                FROM fuel_entry fe
                LEFT JOIN hr_employee emp ON fe.driver_id = emp.id
                GROUP BY fe.vehicle_id, fe.fuel_type, emp.department_id, TO_CHAR(fe.date, 'Month YYYY')
            )
        """)
