/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";


class AssetsDashboard extends Component {
    setup() {
        this.orm = useService("orm");

        this.state = useState({
            total_vacant_slots: 0,
            total_allocated_slots:0,
            total_slots:0,
            today_allocations: 0,
            today_tools_allocations: 0,
            total: 0,
            allocated: 0,
            returned: 0,
            draft: 0,
            allocation_graph: {},
            checklist_graph: {},
            tools_checklist_graph: {},
            camp_checklist_graph: {},
            last_30_days_data: {},
            last_30_days_checklist_data:{},
            allocated_vs_vacant_data:{},
            department_allocation:{},
            camp_data:{},
            groupInfo: {
                is_manager: false,
                is_department: false,
            },
//            tools_allocation_graph:{},


        });

        this.allocationCanvasRef = useRef("chartRef");    // Bar graph
        this.checklistCanvasRef = useRef("chartRefer");  //  Pie graph
        this.departmentCanvasRef=useRef("DepartmentRef")
        this.toolCanvasRef = useRef("statusPieChart");  //  Pie graph
        this.campCanvasRef = useRef("campChart");  // Pie graph
        this.lineChartCanvasRef = useRef("assetLineChart"); //  Line chart canvas
        this.checklistChartCanvasRef = useRef("checklistLine"); //  Line chart canvas
        this.vacancyCanvasRef = useRef("totalrooms"); //  Line chart canvas
        this.campVacancyCanvasRef = useRef("campvacancies"); //  Line chart canvas




        onWillStart(async () => {
            const result = await this.orm.call("assets.dashboard", "get_tiles_data", [], {});
            this.state.total_vacant_slots= result.total_vacant_slots;
            this.state.today_allocations = result.today_allocations;
            this.state.today_tools_allocations = result.today_tools_allocations;
            this.state.total = result.total;
            this.state.allocated = result.allocated;
            this.state.returned = result.returned;
            this.state.draft = result.draft;

            this.state.allocation_graph = result.graph_data || {};
            this.state.checklist_graph = result.check_list_graph_data || {};
            this.state.tools_checklist_graph = result.tools_check_list_graph_data || {};
            this.state.camp_checklist_graph = result.camp_checklist_graph_data || {};
            this.state.last_30_days_data = result.last_30_days_data || {};
            this.state.last_30_days_checklist_data = result.last_30_days_checklist_data || {};
            this.state.allocated_vs_vacant_data = result.allocated_vs_vacant_data || {};
            this.state.stacked_bar_data = result.stacked_bar_data || {};
            this.state.department_allocation = result.department_allocated_graph_data || {};


            const groupInfo = await this.orm.call("assets.dashboard", "get_user_group_info", [], {});
            this.state.groupInfo = groupInfo;






        });

        onMounted(() => {
            this.renderAllocationChart();
            this.renderChecklistChart();
            this.renderToolChecklistChart();
            this.renderDepartmentAllocationChart();
            this.renderCampChecklistChart();
            this.renderLast30DaysChart();
            this.renderChecklistLast30DaysChart();
            this.renderVacancyChart();
            this.renderCampVacancy();


        });
    }
    renderAllocationChart() {
        const canvas = this.allocationCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: Object.keys(this.state.allocation_graph),
                datasets: [{
                    label: 'IT Asset Allocation',
                    data: Object.values(this.state.allocation_graph),
                    backgroundColor: ['#4CAF50', '#2196F3', '#FFC107', '#F44336'],
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                },
                scales: {
                    y: { beginAtZero: true },
                },
            }
        });
    }

    renderChecklistChart() {
        const canvas = this.checklistCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'pie',
            data: {
                labels: Object.keys(this.state.checklist_graph),
                datasets: [{
                    label: 'IT Asset Checklists',
                    data: Object.values(this.state.checklist_graph),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#8BC34A',
                        '#FF9800',
                        '#9C27B0',
                    ],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                }
            }
        });
    }
    renderToolChecklistChart() {
        const canvas = this.toolCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'polarArea',
            data: {
                labels: Object.keys(this.state.tools_checklist_graph),
                datasets: [{
                    label: 'Tool Asset Checklists',
                    data: Object.values(this.state.tools_checklist_graph),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#8BC34A',
                        '#FF9800',
                        '#9C27B0',
                    ],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                }
            }
        });

    }
    renderCampChecklistChart() {
        const canvas = this.campCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'polarArea',
            data: {
                labels: Object.keys(this.state.camp_checklist_graph),
                datasets: [{
                    label: 'Camp Checklists',
                    data: Object.values(this.state.camp_checklist_graph),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#8BC34A',
                        '#FF9800',
                        '#9C27B0',
                    ],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                }
            }
        });
    }
    renderLast30DaysChart() {
        const canvas = this.lineChartCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: Object.keys(this.state.last_30_days_data),
                datasets: [{
                    label: 'Last 30 Days Asset Allocations',
                    data: Object.values(this.state.last_30_days_data),
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54,162,235,0.2)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 1,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                },
                scales: {
                    x: { title: { display: true, text: 'Date' } },
                    y: { title: { display: true, text: 'Allocations' }, beginAtZero: true },
                }
            }
        });
    }


     renderDepartmentAllocationChart() {
        const canvas = this.departmentCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'pie',
            data: {
                labels: Object.keys(this.state.department_allocation),
                datasets: [{
                    label: 'Department Assets Details',
                    data: Object.values(this.state.department_allocation),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#8BC34A',
                        '#FF9800',
                        '#9C27B0',
                        '#4CAF50',
                    ],
                    hoverOffset: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                }
            }
        });
    }
    renderChecklistLast30DaysChart() {
        const canvas = this.checklistChartCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: Object.keys(this.state.last_30_days_checklist_data),
                datasets: [{
                    label: 'Last 30 Days Asset Checklists',
                    data: Object.values(this.state.last_30_days_checklist_data),
                    borderColor: '#36A2EB',
                    tension: 0.3,
                    pointRadius: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                },
                scales: {
                    x: { title: { display: true, text: 'Date' } },
                    y: { title: { display: true, text: 'Allocations' }, beginAtZero: true },
                }
            }
        });
    }
     renderVacancyChart() {
        const canvas = this.vacancyCanvasRef.el;
        if (!canvas) return;

        new Chart(canvas, {
            type: 'doughnut',
            data: {
//        labels: ["Total Rooms","Vacant Rooms"],
                datasets: [{
                    label: 'Vacant Rooms',
                    data: Object.values(this.state.allocated_vs_vacant_data),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#8BC34A',
                        '#FF9800',
                        '#9C27B0',
                    ],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                }
            }
        });
      }
     renderCampVacancy() {
    const canvas = this.campVacancyCanvasRef.el;
    if (!canvas) return;

    new Chart(canvas, {
    type: 'bar',
    data: {
        labels: ["CAMP 1", "CAMP 2", "CAMP 3", "Camp 4"],
        datasets: [
            {
                label: 'Allocated',
                data: Object.values(this.state.stacked_bar_data).map(v => v.allocated || 0),
                backgroundColor: '#E74C3C'
            },
            {
                label: 'Vacant',
                data: Object.values(this.state.stacked_bar_data).map(v => v.vacant || 0),
                backgroundColor: '#F39C12'
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: true, position: 'top' },
        },
        scales: {
            x: { stacked: true },
            y: { stacked: true, beginAtZero: true }
        }
    }
});
}

}

AssetsDashboard.template = "sdm_assets_dashboard.assets_dashboard_template";
registry.category("actions").add("assets_dashboard_tag", AssetsDashboard);