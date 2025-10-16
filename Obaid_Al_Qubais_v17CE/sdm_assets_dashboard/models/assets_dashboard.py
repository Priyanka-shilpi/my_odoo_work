from odoo import models, api
from datetime import datetime, date, timedelta

class AssetsDashboard(models.Model):
    _name = 'assets.dashboard'
    _description = 'Assets Dashboard'

    @api.model
    def get_user_group_info(self):
        user = self.env.user
        return {
            'is_manager': user.has_group('sdm_assets_dashboard.group_manager_access'),
            'is_department': user.has_group('sdm_assets_dashboard.group_department_access'),
        }

    @api.model
    def get_tiles_data(self):


        today = date.today()
        start_datetime = datetime.combine(today, datetime.min.time())
        end_datetime = datetime.combine(today, datetime.max.time())

        # All rooms data
        all_rooms = self.env['camp.room'].search([])
        total_vacant_slots = sum(all_rooms.mapped('vacant_slots'))

        # If total capacity field exists, calculate allocated rooms
        total_capacity = sum(all_rooms.mapped('capacity')) if 'capacity' in all_rooms._fields else 0
        total_allocated_slots = total_capacity - total_vacant_slots if total_capacity else 0

        # Tile: IT asset allocations today
        allocations_today = self.env['it.asset.allocation'].search_count([
            ('allocation_date', '>=', start_datetime),
            ('allocation_date', '<=', end_datetime),
        ])

        # Tile: Tool/Equipment allocations today
        tools_allocations_today = self.env['tools.equipment.allocation'].search_count([
            ('allocation_date', '>=', start_datetime),
            ('allocation_date', '<=', end_datetime),
        ])

        department = self.env['asset.allocation.request'].read_group(
            domain=[],
            fields=['state'],
            groupby=['state'],
            lazy=False
        )
        department_allocation = {r['state']: r['__count'] for r in department}

        # ---- IT Asset Allocation ----
        allocations = self.env['it.asset.allocation'].read_group(
            domain=[],
            fields=['state'],
            groupby=['state'],
            lazy=False
        )
        allocation_graph = {r['state']: r['__count'] for r in allocations}

        # ---- IT Asset Checklist ----
        checklists = self.env['it.asset.checklist'].read_group(
            domain=[],
            fields=['status'],
            groupby=['status'],
            lazy=False
        )
        checklist_graph = {r['status']: r['__count'] for r in checklists}

        # ---- Tools Checklist ----
        tools_checklists = self.env['tools.asset.checklist'].read_group(
            domain=[],
            fields=['status'],
            groupby=['status'],
            lazy=False
        )
        tools_checklist_graph = {r['status']: r['__count'] for r in tools_checklists}

        # ---- Camp Checklist ----
        camp_checklist = self.env['camp.asset.checklist'].read_group(
            domain=[],
            fields=['status'],
            groupby=['status'],
            lazy=False
        )
        camp_checklist_graph = {r['status']: r['__count'] for r in camp_checklist}

        # ---- Last 30 days allocation ----
        last_30_days_data = {}
        for i in range(30):
            day = today - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time())
            end = datetime.combine(day, datetime.max.time())

            count = self.env['it.asset.allocation'].search_count([
                ('create_date', '>=', start),
                ('create_date', '<=', end),
            ])
            last_30_days_data[day.strftime('%Y-%m-%d')] = count
        last_30_days_data = dict(sorted(last_30_days_data.items()))

        # ---- Last 30 days checklist ----
        last_30_days_checklist_data = {}
        for i in range(30):
            day = today - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time())
            end = datetime.combine(day, datetime.max.time())

            count = self.env['it.asset.checklist'].search_count([
                ('create_date', '>=', start),
                ('create_date', '<=', end),
            ])
            last_30_days_checklist_data[day.strftime('%Y-%m-%d')] = count
        last_30_days_checklist_data = dict(sorted(last_30_days_checklist_data.items()))

        # ---- Allocated vs Vacant for Donut Chart ----
        allocated_vs_vacant_data = [
            {"label": "Allocated", "value": total_allocated_slots},
            {"label": "Vacant", "value": total_vacant_slots}
        ]

        stacked_bar_data = []
        room_model = self.env['camp.room']
        has_capacity = 'capacity' in room_model._fields
        has_vacant = 'vacant_slots' in room_model._fields

        camps = self.env['camp.camp'].search([])
        for camp in camps:
            rooms = room_model.search([('block_id.camp_id', '=', camp.id)])

            camp_capacity = sum(rooms.mapped('capacity')) if has_capacity else 0
            camp_vacant = sum(rooms.mapped('vacant_slots')) if has_vacant else 0
            camp_allocated = camp_capacity - camp_vacant if camp_capacity else 0

            stacked_bar_data.append({
                "camp": camp.name,
                "allocated": camp_allocated,
                "vacant": camp_vacant
            })

        return {
            'total_vacant_slots': total_vacant_slots,
            'today_allocations': allocations_today,
            'today_tools_allocations': tools_allocations_today,

            # Allocation Data
            'total': sum(allocation_graph.values()),
            'allocated': allocation_graph.get('allocated', 0),
            'returned': allocation_graph.get('returned', 0),
            'draft': allocation_graph.get('draft', 0),
            'graph_data': allocation_graph,

            # IT Asset Checklist
            'checklist_pending': checklist_graph.get('pending', 0),
            'checklist_verified': checklist_graph.get('verified', 0),
            'checklist_escalated': checklist_graph.get('escalated', 0),
            'check_list_graph_data': checklist_graph,

            # Tools Asset Checklist
            'tools_pending': tools_checklist_graph.get('pending', 0),
            'tools_verified': tools_checklist_graph.get('verified', 0),
            'tools_escalated': tools_checklist_graph.get('escalated', 0),
            'tools_reset': tools_checklist_graph.get('reset', 0),
            'tools_check_list_graph_data': tools_checklist_graph,

            # Camp Checklists
            'camp_pending': camp_checklist_graph.get('pending', 0),
            'camp_verified': camp_checklist_graph.get('verified', 0),
            'camp_escalated': camp_checklist_graph.get('escalated', 0),
            'camp_reset': camp_checklist_graph.get('reset', 0),
            'camp_checklist_graph_data': camp_checklist_graph,

            # 'department_total':sum(department_allocation.values()),
            'department_new': department_allocation.get('new', 0),
            'department_created': department_allocation.get('created', 0),
            'department_pending': department_allocation.get('pending', 0),
            'department_approved': department_allocation.get('approved', 0),
            'department_allocated': department_allocation.get('allocated', 0),
            'department_returned': department_allocation.get('returned', 0),
            'department_rejected': department_allocation.get('rejected', 0),
            'department_allocated_graph_data': department_allocation,

            # Historical Data
            'last_30_days_checklist_data': last_30_days_checklist_data,
            'last_30_days_data': last_30_days_data,

            # Donut Chart Data
            'allocated_vs_vacant_data': allocated_vs_vacant_data,
            'stacked_bar_data': stacked_bar_data
        }

