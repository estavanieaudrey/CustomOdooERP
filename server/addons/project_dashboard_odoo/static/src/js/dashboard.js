/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useRef, useState } from "@odoo/owl";
const { Component, onWillStart } = owl;

export class ProjectDashboard extends Component {
	/**
	 * Setup method to initialize required services and register event handlers.
	 */
	setup() {
		this.action = useService("action");
		this.orm = useService("orm");
		this.project_doughnut = useRef("project_doughnut");
		this.start_date = useRef("start_date");
		this.end_date = useRef("end_date");
		this.tot_project = useRef("tot_project");
		this.tot_employee = useRef("tot_employee");
		this.tot_hrs = useRef("tot_hrs");
		this.tot_margin = useRef("tot_margin");
		this.total_mo = useRef("total_mo");
		this.total_so = useRef("tot_so");
		this.tot_task = useRef("tot_task");
		this.upcoming_deliveries = useRef("upcoming_deliveries");

		// Initialize all required variables
		this.total_bom = 0;
		this.total_tasks = 0;
		this.total_sale_orders = 0;
		this.bom_ids = [];
		this.total_projects = 0;
		this.total_projects_ids = [];
		this.total_hours = 0;
		this.expired_invoices = [];
		this.draft_manufacturing_orders = [];
		this.upcoming_deliveries = [];

		this.rpc = this.env.services.rpc;
		onWillStart(async () => {
		    await this.willStart();
		});
		onMounted(async () => {
			await this.mounted();
		});
	}
	/**
     * Event handler for the 'onWillStart' event.
     */
	async willStart() {
		await this.fetch_data();
	}
	 /**
     * Event handler for the 'onMounted' event.
     * Renders various components and charts after fetching data.
     */
	async mounted() {
		// Render other components after fetching data
		this.render_project_task();
		this.render_top_employees_graph();
	}
	/**
     * Render the project task chart.
     */
	async render_project_task() {
		try {
			console.log('Starting chart render');
			
			if (!this.project_doughnut.el) {
				console.error('Canvas element not found');
				return;
			}

			const result = await rpc('/manufacturing/waste/comparison');
			console.log('Data received:', result);

			if (!result || !result.labels || !result.waste || !result.color) {
				console.error('Invalid data format:', result);
				return;
			}

			const ctx = this.project_doughnut.el.getContext('2d');

			// Destroy existing chart
			if (this.projectDoughnut) {
				this.projectDoughnut.destroy();
			}

			// Create new chart
			this.projectDoughnut = new Chart(ctx, {
				type: 'doughnut',
				data: {
					labels: result.labels.map((label, index) => 
						`${label} (${result.counts[index]} MO)`),
					datasets: [{
						data: result.waste,
						backgroundColor: result.color,
						borderWidth: 0
					}]
				},
				options: {
					responsive: true,
					maintainAspectRatio: true,
					plugins: {
						title: {
							display: true,
							text: 'Perbandingan Surplus Produksi per Jenis Buku',
							font: {
								size: 16
							}
						},
						legend: {
							position: 'bottom',
							display: true
						},
						tooltip: {
							enabled: true,
							callbacks: {
								label: function(context) {
									const label = context.label || '';
									const value = context.raw || 0;
									return `${label}: ${value.toFixed(2)} unit surplus`;
								}
							}
						}
					}
				}
			});
			
			console.log('Chart rendered successfully');
		} catch (error) {
			console.error('Error rendering chart:', error);
		}
	}
	/**
     * Event handler to apply filters based on user selections and update the dashboard data accordingly.
     */
	async _onchangeFilter(ev) {
		this.flag = 1
		var start_date = this.start_date.el.value;
		var end_date = this.end_date.el.value;
		
		if (!start_date) {
			start_date = "null"
		}
		if (!end_date) {
			end_date = "null"
		}
		
		try {
			const data = await this.rpc('/project/filter-apply', {
				'data': {
					'start_date': start_date,
					'end_date': end_date,
					'project': "null",
					'employee': "null"
				}
			});

			if (data) {
				this.tot_hrs = data['list_hours_recorded'] || [];
				this.tot_employee = data['total_emp'] || [];
				this.tot_project = data['total_project'] || [];
				this.tot_mo = data['total_mo'] || [];
				this.tot_so = data['total_so'] || [];

				if (this.tot_project.el) {
					this.tot_project.el.innerHTML = (data['total_project'] || []).length;
				}
				if (this.tot_employee.el) {
					this.tot_employee.el.innerHTML = (data['total_emp'] || []).length;
				}
				if (this.total_mo.el) {
					this.total_mo.el.innerHTML = (data['total_mo'] || []).length;
				}
				if (this.tot_hrs.el) {
					this.tot_hrs.el.innerHTML = 'Rp ' + this.formatToRupiah(Math.round(data['hours_recorded'] || 0));
				}
				if (this.tot_margin.el) {
					this.tot_margin.el.innerHTML = 'Rp ' + this.formatToRupiah(Math.round(data['total_margin'] || 0));
				}
				if (this.total_so.el) {
					this.total_so.el.innerHTML = (data['total_so'] || []).length;
				}
			}
		} catch (error) {
			console.error('Error in filter application:', error);
		}
	}
	/**
     * Event handler to open a list of employees and display them to the user.
     */
	tot_emp(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Employees"),
				type: 'ir.actions.act_window',
				res_model: 'hr.employee',
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options)
		} else {
			this.action.doAction({
				name: _t("Employees"),
				type: 'ir.actions.act_window',
				res_model: 'hr.employee',
				domain: [
					["id", "in", this.tot_employee]
				],
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options)
		}
	}
	/**
	 * Format number to Indonesian Rupiah
	 * @param {number} number - Number to format
	 * @returns {string} Formatted number in Indonesian Rupiah
	 */
	formatToRupiah(number) {
		return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
	}
	/**
	function for getting values when page is loaded
	*/
	async fetch_data() {
		this.flag = 0
		var self = this;
		try {
			const def1 = await rpc('/get/tiles/data').then(function(result) {
				if (result['flag'] == 1) {
					self.total_bom = result['total_bom'] || 0;
					self.bom_ids = result['bom_ids'] || [];
					self.total_hours = self.formatToRupiah(Math.round(result['total_hours'] || 0));
					self.total_profitability = self.formatToRupiah(Math.round(result['total_profitability'] || 0));
					self.total_employees = result['total_employees'] || 0;
					self.total_sale_orders = result['total_sale_orders'] || 0;
					self.tot_so = result['sale_orders_ids'] || [];
					self.flag_user = result['flag'];
					self.total_tasks = result['total_mo'] || 0;
				} else {
					self.total_bom = result['total_bom'] || 0;
					self.bom_ids = result['bom_ids'] || [];
					self.total_hours = self.formatToRupiah(Math.round(result['total_hours'] || 0));
					self.total_profitability = self.formatToRupiah(Math.round(result['total_profitability'] || 0));
					self.total_sale_orders = result['total_sale_orders'] || 0;
					self.flag_user = result['flag'];
					self.tot_so = result['sale_orders_ids'] || [];
					self.total_tasks = result['total_mo'] || 0;
				}
			});

			const def2 = await rpc('/get/expired/orders')
				.then(function(res) {
					self.expired_sale_orders = res.map(order => ({
						...order,
						order_id: order.order_id || order.id
					}));
				});

			const def3 = await rpc('/get/expired/invoices')
				.then(function(res) {
					self.expired_invoices = res.map(invoice => ({
						...invoice,
						invoice_id: invoice.invoice_id || invoice.id
					}));
				});

			const def4 = await rpc('/get/draft/manufacturing')
				.then(function(res) {
					console.log('Raw Manufacturing orders response:', res);
					
					if (!res) {
						console.error('No response received from server');
						self.draft_manufacturing_orders = [];
						return;
					}
					
					if (!Array.isArray(res)) {
						console.error('Response is not an array:', res);
						self.draft_manufacturing_orders = [];
						return;
					}
					
					self.draft_manufacturing_orders = res.map(mo => ({
						...mo,
						mo_id: mo.mo_id || mo.id,
						state: mo.state || 'draft'
					}));
				})
				.catch(error => {
					console.error('Error details:', {
						message: error.message,
						status: error.status,
						data: error.data,
						stack: error.stack
					});
					self.draft_manufacturing_orders = [];
				});

			const def5 = await rpc('/get/upcoming/deliveries')
				.then(function(res) {
					console.log('Raw Delivery orders response:', res);
					
					if (!res) {
						console.error('No response received from server');
						self.upcoming_deliveries = [];
						return;
					}
					
					if (!Array.isArray(res)) {
						console.error('Response is not an array:', res);
						self.upcoming_deliveries = [];
						return;
					}
					
					self.upcoming_deliveries = res.map(delivery => ({
						...delivery,
						picking_id: delivery.picking_id || delivery.id
					}));
				})
				.catch(error => {
					console.error('Error details:', {
						message: error.message,
						status: error.status,
						data: error.data,
						stack: error.stack
					});
					self.upcoming_deliveries = [];
				});

			return Promise.all([def1, def2, def3, def4, def5]);
		} catch (error) {
			console.error('Error fetching data:', error);
			// Set default values if error occurs
			this.total_bom = 0;
			this.total_tasks = 0;
			this.total_sale_orders = 0;
			this.bom_ids = [];
			this.total_profitability = this.formatToRupiah(0);
			this.expired_sale_orders = [];
			this.expired_invoices = [];
			this.draft_manufacturing_orders = [];
			this.upcoming_deliveries = [];
		}
	}
	/**
     * Event handler to open list of Bill of Materials
     */
	tot_projects(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		this.action.doAction({
			name: _t("Bills of Materials"),
			type: 'ir.actions.act_window',
			res_model: 'mrp.bom',
			view_mode: 'tree,form',
			views: [
				[false, 'list'],
				[false, 'form']
			],
			target: 'current'
		}, options)
	}
	/**
     * Event handler to open a list of tasks and display them to the user.
     */
	async tot_tasks(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		this.action.doAction({
			name: _t("Manufacturing Orders"),
			type: 'ir.actions.act_window',
			res_model: 'mrp.production',
			view_mode: 'tree,form',
			views: [
				[false, 'list'],
				[false, 'form']
			],
			target: 'current'
		}, options)
	}
	/**
	for opening account analytic line view
	*/
	hr_recorded(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Timesheets"),
				type: 'ir.actions.act_window',
				res_model: 'account.analytic.line',
				view_mode: 'tree,form',
				views: [
					[false, 'list']
				],
				target: 'current'
			}, options)
		} else {
			if (this.tot_hrs) {
				this.action.doAction({
					name: _t("Timesheets"),
					type: 'ir.actions.act_window',
					res_model: 'account.analytic.line',
					domain: [
						["id", "in", this.tot_hrs]
					],
					view_mode: 'tree,form',
					views: [
						[false, 'list']
					],
					target: 'current'
				}, options)
			}
		}
	}
	/**
	for opening vendor bill list view when clicking Hours Recorded
	*/
	async tot_vendorbill(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Vendor Bills"),
				type: 'ir.actions.act_window',
				res_model: 'account.move',
				domain: [
					['move_type', '=', 'in_invoice'],
					['state', '=', 'posted']
				],
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current',
				context: {
					'default_move_type': 'in_invoice',
				}
			}, options);
		} else {
			// If filtered data exists, show only filtered vendor bills
			const start_date = this.start_date.el.value;
			const end_date = this.end_date.el.value;
			let domain = [
				['move_type', '=', 'in_invoice'],
				['state', '=', 'posted']
			];
			
			if (start_date && end_date) {
				domain.push(['invoice_date', '>=', start_date]);
				domain.push(['invoice_date', '<=', end_date]);
			}
			
			this.action.doAction({
				name: _t("Vendor Bills"),
				type: 'ir.actions.act_window',
				res_model: 'account.move',
				domain: domain,
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current',
				context: {
					'default_move_type': 'in_invoice',
				}
			}, options);
		}
	}
	/**
	for opening account move view when clicking Total Margin
	*/
	async tot_invoice(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		
		if (this.flag == 0) {
			this.action.doAction({
				name: _t("Invoices"),
				type: 'ir.actions.act_window',
				res_model: 'account.move',
				domain: [['move_type', 'in', ['out_invoice', 'out_refund']]],
				// domain: [
				// 	['move_type', 'in', ['out_invoice', 'out_refund']],
				// 	['payment_state', 'in', ['in_payment', 'paid', 'partial']]
				// ],
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options);
		} else {
			// If filtered data exists, show only filtered invoices
			const start_date = this.start_date.el.value;
			const end_date = this.end_date.el.value;
			let domain = [['move_type', 'in', ['out_invoice', 'out_refund']]];
			// let domain = [
			// 	['move_type', 'in', ['out_invoice', 'out_refund']],
			// 	['payment_state', 'in', ['in_payment', 'paid', 'partial']]
			// ];
			
			if (start_date && end_date) {
				domain.push(['invoice_date', '>=', start_date]);
				domain.push(['invoice_date', '<=', end_date]);
			}
			
			this.action.doAction({
				name: _t("Invoices"),
				type: 'ir.actions.act_window',
				res_model: 'account.move',
				domain: domain,
				view_mode: 'tree,form',
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			}, options);
		}
	}

	/**
	for opening sale order view
	*/
	async tot_sale(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		this.action.doAction({
			name: _t("Sales Orders"),
			type: 'ir.actions.act_window',
			res_model: 'sale.order',
			view_mode: 'list,form',
			views: [
				[false, 'list'],
				[false, 'form']
			],
			target: 'current'
		}, options);
	}
	/**
     * Event handler to open list of Bill of Materials
     */
	async tot_bom(e) {
		e.stopPropagation();
		e.preventDefault();
		var options = {
			on_reverse_breadcrumb: this.on_reverse_breadcrumb,
		};
		this.action.doAction({
			name: _t("Bills of Materials"),
			type: 'ir.actions.act_window',
			res_model: 'mrp.bom',
			view_mode: 'tree,form',
			views: [
				[false, 'list'],
				[false, 'form']
			],
			target: 'current'
		}, options)
	}
}
ProjectDashboard.template = "ProjectDashboard"
registry.category("actions").add("project_dashboard", ProjectDashboard)
