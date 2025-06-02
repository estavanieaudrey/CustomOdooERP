/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useRef, useState } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
const { Component, onWillStart } = owl;

export class ProjectDashboard extends Component {
	/**
	 * Setup method to initialize required services and register event handlers.
	 */
	setup() {
		this.action = useService("action");
		this.orm = useService("orm");
		this.dialog = useService("dialog"); // Tambahkan dialog service
		this.project_doughnut = useRef("project_doughnut");
		this.start_date = useRef("start_date");
		this.end_date = useRef("end_date");
		this.filterBtn = useRef("filterBtn");
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
		// Pastikan elemen DOM tersedia sebelum memanggil fungsi
		await this.render_project_task();
    	await this._renderTables(); // Add this line
		// await this.render_top_employees_graph();
	}
	/**
     * Render the project task chart.
     */
	async render_project_task(start_date = null, end_date = null) {
		try {
			console.log('Starting chart render with filters:', { start_date, end_date });
			
			if (!this.project_doughnut.el) {
				console.error('Canvas element not found');
				return;
			}
	
			// Pass the date filters to the RPC call
			const result = await rpc('/manufacturing/waste/comparison', {
				data: {
					start_date: start_date,
					end_date: end_date,
				},
			});
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
					labels: result.labels.map((label, index) => {
						const totalWaste = result.waste.reduce((acc, value) => acc + value, 0); // Hitung total waste
						const percentage = ((result.waste[index] / totalWaste) * 100).toFixed(2); // Hitung persentase
						return `${label} (${result.counts[index]} MO, ${percentage}%)`; // Tambahkan total MO dan persentase
					}),
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
									const totalWaste = context.chart.data.datasets[0].data.reduce((acc, val) => acc + val, 0); // Hitung total waste
									const percentage = ((value / totalWaste) * 100).toFixed(2); // Hitung persentase
									return `${label}: ${value.toFixed(2)} unit surplus (${percentage}%)`; // Tampilkan total MO dan persentase
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
	async _renderTables() {

		console.log('Rendering tables with data:', {
			'expired_sale_orders': this.expired_sale_orders?.length || 0,
			'draft_manufacturing_orders': this.draft_manufacturing_orders?.length || 0,
			'upcoming_deliveries': this.upcoming_deliveries?.length || 0,
			'expired_invoices': this.expired_invoices?.length || 0
		});

		// 1. Update expired sale orders table
		const expiredSalesTable = document.querySelector('.expired-sale-orders-table tbody');
		if (expiredSalesTable) {
			expiredSalesTable.innerHTML = '';
			if (this.expired_sale_orders && this.expired_sale_orders.length > 0) {
				this.expired_sale_orders.forEach(order => {
					const row = document.createElement('tr');
					row.innerHTML = `
						<td><a href="/web#id=${order.order_id}&model=sale.order&view_type=form" target="_blank">${order.name}</a></td>
						<td>${order.partner_name || ''}</td>
						<td>${order.product_name || ''}</td>
						<td>${order.product_qty || ''}</td>
						<td>${order.expired_date || ''}</td>
					`;
					expiredSalesTable.appendChild(row);
				});
			} else {
				expiredSalesTable.innerHTML = '<tr><td colspan="5" class="text-center">No expired sale orders</td></tr>';
			}
		}
		
		// 2. Update draft manufacturing orders table
		const draftMOTable = document.querySelector('.draft-manufacturing-orders-table tbody');
		if (draftMOTable) {
			draftMOTable.innerHTML = '';
			if (this.draft_manufacturing_orders && this.draft_manufacturing_orders.length > 0) {
				this.draft_manufacturing_orders.forEach(mo => {
					console.log("MO data:", mo); // Debug log untuk melihat data yang diterima
					const row = document.createElement('tr');
					row.innerHTML = `
						<td><a href="/web#id=${mo.mo_id}&model=mrp.production&view_type=form" target="_blank">${mo.name}</a></td>
						<td>${mo.product_name || ''}</td>
						<td>${mo.user_name || ''}</td>
						<td>${mo.tanggal_spk || ''}</td>
						<td>${mo.product_qty || ''}</td>
						<td>${mo.nama_customer || ''}</td>
						<td>${mo.origin || ''}</td>
						<td>${this.getStatusBadge(mo.state) || ''}</td>
					`;
					draftMOTable.appendChild(row);
				});
			} else {
				draftMOTable.innerHTML = '<tr><td colspan="8" class="text-center">No draft manufacturing orders</td></tr>';
			}
		}
		
		// 3. Update upcoming deliveries table
		const upcomingDeliveriesTable = document.querySelector('.upcoming-deliveries-table tbody');
		if (upcomingDeliveriesTable) {
			upcomingDeliveriesTable.innerHTML = '';
			if (this.upcoming_deliveries && this.upcoming_deliveries.length > 0) {
				this.upcoming_deliveries.forEach(delivery => {
					console.log("Delivery data:", delivery); // Debug untuk melihat data
					const row = document.createElement('tr');
					row.innerHTML = `
						<td><a href="/web#id=${delivery.picking_id}&model=stock.picking&view_type=form" target="_blank">${delivery.reference || delivery.name || ''}</a></td>
						<td>${delivery.partner_name || ''}</td>
						<td>${delivery.product_names || ''}</td>
						<td>${delivery.total_quantity || ''}</td>
						<td>${delivery.date_deadline || delivery.scheduled_date || ''}</td>
						<td>${this.getStatusBadge(delivery.state) || ''}</td>
					`;
					upcomingDeliveriesTable.appendChild(row);
				});
			} else {
				upcomingDeliveriesTable.innerHTML = '<tr><td colspan="6" class="text-center">No upcoming deliveries</td></tr>';
			}
		}
		
		// 4. Update expired invoices table
		const expiredInvoicesTable = document.querySelector('.expired-invoices-table tbody');
		if (expiredInvoicesTable) {
			expiredInvoicesTable.innerHTML = '';
			if (this.expired_invoices && this.expired_invoices.length > 0) {
				this.expired_invoices.forEach(invoice => {
					console.log("Invoice data:", invoice); // Debug untuk melihat data
					const row = document.createElement('tr');
					row.innerHTML = `
						<td><a href="/web#id=${invoice.invoice_id}&model=account.move&view_type=form" target="_blank">${invoice.name}</a></td>
						<td>${invoice.invoice_date_due || ''}</td>
						<td>${this.formatToRupiah(invoice.amount_total_in_currency_signed || 0)}</td>
                		<td>${this.getPaymentStateBadge(invoice.payment_state || '')}</td>
					`;
					expiredInvoicesTable.appendChild(row);
				});
			} else {
				expiredInvoicesTable.innerHTML = '<tr><td colspan="4" class="text-center">No expired invoices</td></tr>';
			}
		}
	}
	
	// Tambahkan helper function untuk menampilkan status
	getStatusBadge(state) {
		const stateMapping = {
			'draft': '<span class="badge bg-secondary">Draft</span>',
			'waiting': '<span class="badge bg-info">Waiting</span>',
			'confirmed': '<span class="badge bg-primary">Confirmed</span>',
			'assigned': '<span class="badge bg-success">Ready</span>',
			'done': '<span class="badge bg-success">Done</span>',
			'cancel': '<span class="badge bg-danger">Cancelled</span>',
			'progress': '<span class="badge bg-warning">In Progress</span>'
		};
		
		return stateMapping[state] || `<span class="badge bg-secondary">${state}</span>`;
	}

	getPaymentStateBadge(state) {
		const stateMapping = {
			'paid': '<span class="badge bg-success">Paid</span>',
			'in_payment': '<span class="badge bg-warning">In Payment</span>',
			'not_paid': '<span class="badge bg-danger">Not Paid</span>',
			'partial': '<span class="badge bg-info">Partial</span>',
			'reversed': '<span class="badge bg-secondary">Reversed</span>',
			'invoicing_legacy': '<span class="badge bg-secondary">Legacy</span>'
		};
		
		return stateMapping[state] || `<span class="badge bg-secondary">${state}</span>`;
	}

	_onStartDateChange(ev) {
		const startDate = ev.target.value;
		const endDate = this.end_date.el.value;
		
		if (startDate && endDate) {
			const startDateObj = new Date(startDate);
			const endDateObj = new Date(endDate);
			
			if (endDateObj < startDateObj) {
				this.end_date.el.value = '';
				
				// Gunakan AlertDialog langsung
				this.dialog.add(AlertDialog, {
					title: 'Peringatan',
					body: 'End Date telah direset karena lebih awal dari Start Date',
					confirmLabel: 'OK',
				});
			}
		}
	}

	_onEndDateChange(ev) {
		const endDate = ev.target.value;
		const startDate = this.start_date.el.value;
		
		if (startDate && endDate) {
			const startDateObj = new Date(startDate);
			const endDateObj = new Date(endDate);
			
			if (endDateObj < startDateObj) {
				ev.target.value = '';
				
				// Gunakan AlertDialog langsung
				this.dialog.add(AlertDialog, {
					title: 'Error Validasi',
					body: 'End Date tidak boleh lebih awal dari Start Date!',
					confirmLabel: 'OK',
				});
			}
		}
	}

	async _onchangeFilter(ev) {
		const start_date = this.start_date.el.value || null;
		const end_date = this.end_date.el.value || null;

		// Validasi tanggal
		if (start_date && end_date) {
			const startDateObj = new Date(start_date);
			const endDateObj = new Date(end_date);
			
			if (endDateObj < startDateObj) {
				this.dialog.add(AlertDialog, {
					title: 'Error Validasi Tanggal',
					body: 'End Date tidak boleh lebih awal dari Start Date!',
					confirmLabel: 'OK',
				});
				
				// Reset end date
				this.end_date.el.value = '';
				return;
			}
		}
	
		try {
			console.log("Filter applied with start_date:", start_date, "end_date:", end_date);
	
			// Menampilkan loading indicator
			this.isLoading = true;
			
			const data = await rpc('/project/filter-apply', {
				data: {
					start_date: start_date,
					end_date: end_date,
				},
			});

			// Check untuk error dari backend
			if (data.error) {
				this.dialog.add(AlertDialog, {
					title: 'Error Filter',
					body: data.message || "Terjadi kesalahan dalam filter",
					confirmLabel: 'OK',
				});
				this.end_date.el.value = '';
				this.isLoading = false;
				return;
			}
	
			console.log("Data received from filter:", data);
	
			// Update dashboard elements
			if (this.tot_task.el) {
				this.tot_task.el.innerHTML = data.total_tasks || 0;
			}
			if (this.tot_hrs.el) {
				this.tot_hrs.el.innerHTML = 'Rp ' + this.formatToRupiah(data.total_vendorbills || 0);
			}
			if (this.tot_margin.el) {
				this.tot_margin.el.innerHTML = 'Rp ' + this.formatToRupiah(data.total_margin || 0);
			}
			if (this.total_so.el) {
				this.total_so.el.innerHTML = data.total_sale_orders || 0;
			}
	
			// Update the component's data properties with filtered data
			this.expired_sale_orders = data.expired_sale_orders || [];
			this.draft_manufacturing_orders = data.draft_manufacturing_orders || [];
			this.upcoming_deliveries = data.upcoming_deliveries || [];
			this.expired_invoices = data.expired_invoices || [];
	
			// Render tables with the new filtered data
			await this._renderTables();
			
			// Re-render chart with filter parameters
			await this.render_project_task(start_date, end_date);

			// Matikan loading indicator
			this.isLoading = false;
		} catch (error) {
			console.error('Error in filter application:', error);
			// Tampilkan error dengan handling yang lebih baik
			try {
				if (this.env.services.dialog) {
					this.env.services.dialog.add('web.AlertDialog', {
						title: 'Error Sistem',
						body: 'Terjadi kesalahan saat melakukan filter. Silakan coba lagi.',
						confirmLabel: 'OK',
					});
				} else {
					alert('Terjadi kesalahan saat melakukan filter. Silakan coba lagi.');
				}
			} catch (dialogError) {
				console.error('Error showing dialog:', dialogError);
				alert('Terjadi kesalahan saat melakukan filter. Silakan coba lagi.');
			}

			this.isLoading = false;
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
