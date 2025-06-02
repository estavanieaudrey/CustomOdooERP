# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import datetime
import logging
from odoo import http
from odoo.http import request
import traceback

_logger = logging.getLogger(__name__)

class ProjectFilter(http.Controller):
    """The ProjectFilter class provides the filter option to the js.
    When applying the filter returns the corresponding data."""

    @http.route('/project/task/count', auth='public', type='json')
    def get_project_task_count(self):
        """Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data for
            the manufacturing orders graph."""
        project_name = []
        total_mo = []
        colors = []
        if request.env.user.has_group('project.group_project_manager'):
            project_ids = request.env['project.project'].search([])
        else:
            project_ids = request.env['project.project'].search(
                [('user_id', '=', request.env.uid)])
        for project_id in project_ids:
            project_name.append(project_id.name)
            mo_count = request.env['mrp.production'].search_count([])
            total_mo.append(mo_count)
            color_code = request.env['project.project'].get_color_code()
            colors.append(color_code)
        return {
            'project': project_name,
            'task': total_mo,  # Keeping 'task' key for compatibility with existing JS
            'color': colors
        }

    @http.route('/employee/timesheet', auth='public', type='json')
    def get_top_timesheet_employees(self):
        """Summary:
            when the page is loaded, get the data for the timesheet graph.
        Return:
            type:It is a list. This list contains data that affects the graph
            of employees."""
        query = '''select hr_employee.name as employee,sum(unit_amount) as unit
                    from account_analytic_line
                    inner join hr_employee on hr_employee.id =
                    account_analytic_line.employee_id
                    group by hr_employee.id ORDER 
                    BY unit DESC Limit 10 '''
        request._cr.execute(query)
        top_product = request._cr.dictfetchall()
        unit = [record.get('unit') for record in top_product]
        employee = [record.get('employee') for record in top_product]
        return [unit, employee]

    @http.route('/project/filter', auth='public', type='json')
    def project_filter(self):
        """Summary:
            transferring data to the selection field that works as a filter
        Returns:
            type:list of lists, it contains the data for the corresponding
            filter."""
        project_list = []
        employee_list = []
        project_ids = request.env['project.project'].search([])
        employee_ids = request.env['hr.employee'].search([])
        # getting partner data
        for employee_id in employee_ids:
            dic = {'name': employee_id.name,
                   'id': employee_id.id}
            employee_list.append(dic)
        for project_id in project_ids:
            dic = {'name': project_id.name,
                   'id': project_id.id}
            project_list.append(dic)
        return [project_list, employee_list]

    @http.route('/project/filter-apply', auth='public', type='json')
    def project_filter_apply(self, **kw):
        """Filter data based on start_date and end_date."""
        data = kw['data']
        start_date = data['start_date']
        end_date = data['end_date']
        
        _logger.info("Filter applied with start_date: %s, end_date: %s", start_date, end_date)

        # Konversi tanggal dari string ke format date
        if start_date != 'null' and start_date:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date = None

        if end_date != 'null' and end_date:
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            end_date = None
            
        # Validasi tanggal - pastikan end_date tidak lebih awal dari start_date
        if start_date and end_date and end_date < start_date:
            return {
                'error': True,
                'message': 'End Date tidak boleh lebih awal dari Start Date!',
                'total_tasks': 0,
                'total_vendorbills': 0,
                'total_margin': 0,
                'total_sale_orders': 0,
                'expired_sale_orders': [],
                'draft_manufacturing_orders': [],
                'upcoming_deliveries': [],
                'expired_invoices': [],
            }


        # Filter Manufacturing Orders (tot_tasks)
        mo_domain = []
        if start_date:
            mo_domain.append(('date_start', '>=', start_date))
        if end_date:
            mo_domain.append(('date_start', '<=', end_date))
        manufacturing_orders = request.env['mrp.production'].search(mo_domain)

        # Filter Vendor Bills (tot_vendorbill)
        bill_domain = [('move_type', '=', 'in_invoice'), ('state', '=', 'posted')]
        if start_date:
            bill_domain.append(('invoice_date', '>=', start_date))
        if end_date:
            bill_domain.append(('invoice_date', '<=', end_date))
        vendor_bills = request.env['account.move'].search(bill_domain)

        # Filter Invoices (tot_invoice)
        invoice_domain = [('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')]
        if start_date:
            invoice_domain.append(('invoice_date', '>=', start_date))
        if end_date:
            invoice_domain.append(('invoice_date', '<=', end_date))
        invoices = request.env['account.move'].search(invoice_domain)

        # Filter Sale Orders (with date_order)
        sale_order_domain = []
        if start_date:
            sale_order_domain.append(('date_order', '>=', start_date))
        if end_date:
            sale_order_domain.append(('date_order', '<=', end_date))
        sale_orders = request.env['sale.order'].search(sale_order_domain)
        
        # Format expired sale orders (ambil hanya satu entri per sale order)
        expired_sale_orders = []
        for order in sale_orders:
            expired_sale_orders.append({
                'order_id': order.id,
                'name': order.name,
                'partner_name': order.partner_id.name,
                'product_name': ', '.join(order.order_line.mapped('product_id.name')),  # Gabungkan nama produk
                'product_qty': sum(order.order_line.mapped('product_uom_qty')),  # Total kuantitas produk
                'expired_date': order.date_order.strftime('%Y-%m-%d') if order.date_order else '',
            })


        # Filter Manufacturing Orders with date_start
        mo_domain = [('state', 'in', ['draft', 'confirmed', 'progress'])]
        if start_date:
            mo_domain.append(('date_start', '>=', start_date))
        if end_date:
            mo_domain.append(('date_start', '<=', end_date))
        
        manufacturing_orders = request.env['mrp.production'].search(mo_domain)
        draft_manufacturing_orders = []
        for mo in manufacturing_orders:
            origin = mo.origin or ''
            customer_name = ''
            if mo.procurement_group_id and mo.procurement_group_id.sale_id:
                customer_name = mo.procurement_group_id.sale_id.partner_id.name
                
            draft_manufacturing_orders.append({
                'mo_id': mo.id,
                'name': mo.name,
                'product_name': mo.product_id.name,
                'user_name': mo.user_id.name if mo.user_id else '',
                'tanggal_spk': mo.create_date.strftime('%Y-%m-%d') if mo.create_date else '',
                'product_qty': mo.product_qty,
                'nama_customer': customer_name,
                'origin': origin,
                'state': mo.state,
            })

        # Filter Upcoming Deliveries with scheduled_date
        delivery_domain = [('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned'])]
        if start_date:
            delivery_domain.append(('scheduled_date', '>=', start_date))
        if end_date:
            delivery_domain.append(('scheduled_date', '<=', end_date))
        
        picking_type_ids = request.env['stock.picking.type'].search([('code', '=', 'outgoing')]).ids
        if picking_type_ids:
            delivery_domain.append(('picking_type_id', 'in', picking_type_ids))
            
        upcoming_deliveries = request.env['stock.picking'].search(delivery_domain)
        upcoming_deliveries_data = []
        
        for picking in upcoming_deliveries:
            product_names = []
            total_qty = 0
            for move in picking.move_ids:
                product_names.append(move.product_id.name)
                total_qty += move.product_uom_qty
                
            upcoming_deliveries_data.append({
                'picking_id': picking.id,
                'reference': picking.name,
                'partner_name': picking.partner_id.name if picking.partner_id else '',
                'product_names': ', '.join(product_names),
                'total_quantity': total_qty,
                'date_deadline': picking.date_deadline.strftime('%Y-%m-%d') if picking.date_deadline else '',
                'state': picking.state,
            })

        # Filter Expired Invoices with invoice_date
        invoice_domain = [('move_type', 'in', ['out_invoice', 'out_refund'])]
        if start_date:
            invoice_domain.append(('invoice_date', '>=', start_date))
        if end_date:
            invoice_domain.append(('invoice_date', '<=', end_date))
        
        expired_invoices = request.env['account.move'].search(invoice_domain)
        expired_invoices_data = []
        
        for invoice in expired_invoices:
            expired_invoices_data.append({
                'invoice_id': invoice.id,
                'name': invoice.name,
                'partner_name': invoice.partner_id.name if invoice.partner_id else '',
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
                'invoice_date_due': invoice.invoice_date_due.strftime('%Y-%m-%d') if invoice.invoice_date_due else '',
                'amount_total': invoice.amount_total,
                'amount_total_in_currency_signed': invoice.amount_total_signed,
                'payment_state': invoice.payment_state,
            })


        # Hitung total untuk KPI cards
        return {
            'total_tasks': len(manufacturing_orders),
            'total_vendorbills': sum(vendor_bills.mapped('amount_total')),
            'total_margin': sum(invoices.mapped('amount_total')),
            'total_sale_orders': len(sale_orders),
            'expired_sale_orders': expired_sale_orders,
            'draft_manufacturing_orders': draft_manufacturing_orders,
            'upcoming_deliveries': upcoming_deliveries_data,
            'expired_invoices': expired_invoices_data,
        }
        # # Aktifkan kembali kode yang mengembalikan data terfilter
        # return {
        #     'total_tasks': len(manufacturing_orders),
        #     'total_vendorbills': sum(vendor_bills.mapped('amount_total')),
        #     'total_margin': sum(invoices.mapped('amount_total')),
        #     'total_sale_orders': len(sale_orders),
        #     'expired_sale_orders': expired_sale_orders.read(['name', 'partner_id', 'date_order']),
        #     'draft_manufacturing_orders': draft_manufacturing_orders.read(['name', 'date_start', 'state']),
        #     'upcoming_deliveries': upcoming_deliveries.read(['name', 'scheduled_date', 'state']),
        #     'expired_invoices': expired_invoices.read(['name', 'invoice_date', 'amount_total']),
        # }
        
    @http.route('/manufacturing/waste/comparison', type='json', auth='user')
    def get_manufacturing_waste_comparison(self, **kw):
        """
        Mengambil data perbandingan waste (surplus_qty) antara buku A4 dan B5
        berdasarkan product_id dari manufacturing orders dengan filter tanggal.
        """
        try:
            # Extract date filter parameters if provided
            data = kw.get('data', {})
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            _logger.info(f"Waste comparison filter applied with start_date: {start_date}, end_date: {end_date}")
            
            # Inisialisasi hasil
            result = {
                'labels': ['A4', 'B5'],
                'waste': [0.0, 0.0],
                'color': ['#BE1B4B', '#1FF15B'],
                'counts': [0, 0]
            }

            # Cari products dengan kode A4 dan B5
            products = request.env['product.product'].search([
                ('default_code', 'in', ['A4', 'B5'])
            ])

            # Buat dictionary untuk mapping product
            product_map = {
                p.default_code: p.id for p in products
            }

            _logger.info(f"Product mapping: {product_map}")

            # Build domain for filtered MOs
            domain = [
                ('state', '=', 'done'),
                ('surplus_qty', '>', 0.0)
            ]
            
            # Add date filters if provided
            if start_date and start_date != 'null':
                try:
                    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                    domain.append(('date_start', '>=', start_date))
                except Exception as e:
                    _logger.error(f"Error parsing start_date: {e}")
                    
            if end_date and end_date != 'null':
                try:
                    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                    domain.append(('date_start', '<=', end_date))
                except Exception as e:
                    _logger.error(f"Error parsing end_date: {e}")
            
            # Cari MO yang sudah selesai dan punya surplus dengan filter tanggal
            mos = request.env['mrp.production'].search(domain)

            _logger.info(f"Total MOs found with filters: {len(mos)}, domain: {domain}")

            # Hitung total surplus untuk masing-masing tipe
            for mo in mos:
                if mo.product_id.id == product_map.get('A4'):
                    result['waste'][0] += mo.surplus_qty
                    result['counts'][0] += 1
                    _logger.info(f"Added A4 surplus: {mo.surplus_qty}")
                elif mo.product_id.id == product_map.get('B5'):
                    result['waste'][1] += mo.surplus_qty
                    result['counts'][1] += 1
                    _logger.info(f"Added B5 surplus: {mo.surplus_qty}")

            _logger.info(f"Final result with filters: {result}")
            return result

        except Exception as e:
            _logger.error(f"Error in waste comparison: {str(e)}")
            return {
                'labels': ['A4', 'B5'],
                'waste': [0.0, 0.0],
                'color': ['#BE1B4B', '#1FF15B'],
                'counts': [0, 0]
            }
            
    def get_total_invoices(self):
        """Calculate total amount of invoices with specific payment states."""
        domain = [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('payment_state', 'in', ['in_payment', 'paid', 'partial']),
            ('state', '=', 'posted')
        ]
        invoices = request.env['account.move'].search(domain)
        total_amount = sum(invoices.mapped('amount_total'))
        return total_amount

    def get_total_vendorbills(self):
        """Calculate total amount of posted vendor bills."""
        domain = [
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted')
        ]
        vendor_bills = request.env['account.move'].search(domain)
        total_amount = sum(vendor_bills.mapped('amount_total'))
        return total_amount

    @http.route('/get/tiles/data', auth='public', type='json')
    def get_tiles_data(self):
        """Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
        Return:
            type:It is a dictionary variable. This dictionary contains data that
             affects the dashboard view."""
        if request.env.user.has_group('project.group_project_manager'):
            # Get BOM count
            bom_count = request.env['mrp.bom'].search_count([])
            bom_ids = request.env['mrp.bom'].search([]).ids
            
            # Get manufacturing orders count
            mo_orders = request.env['mrp.production'].search([])
            
            analytic_project = request.env['account.analytic.line'].search([])
            report_project = request.env['timesheets.analysis.report'].search([])
            margin = round(sum(report_project.mapped('margin')), 2)
            
            # Get total vendor bills amount
            total_vendorbills = self.get_total_vendorbills()
            
            employees = request.env['hr.employee'].search([])
            sale_orders = request.env['sale.order'].search([])
            
            # Get total invoices amount
            total_invoices = self.get_total_invoices()
            
            return {
                'total_bom': bom_count,
                'bom_ids': bom_ids,
                'total_mo': len(mo_orders),
                'total_mo_ids': mo_orders.ids,
                'total_hours': round(total_vendorbills, 2),  # Updated to show total vendor bills
                'total_profitability': round(total_invoices, 2),
                'total_employees': len(employees),
                'total_sale_orders': len(sale_orders),
                'sale_orders_ids': sale_orders.ids,
                'flag': 1
            }
        else:
            # Get BOM count for current user
            bom_count = request.env['mrp.bom'].search_count([('user_id', '=', request.env.uid)])
            bom_ids = request.env['mrp.bom'].search([('user_id', '=', request.env.uid)]).ids
            
            # Get manufacturing orders for current user
            mo_orders = request.env['mrp.production'].search([('user_id', '=', request.env.uid)])
            
            # Get total vendor bills amount
            total_vendorbills = self.get_total_vendorbills()
            
            sale_orders = request.env['sale.order'].search([('user_id', '=', request.env.uid)])
            
            # Get total invoices amount
            total_invoices = self.get_total_invoices()
            
            return {
                'total_bom': bom_count,
                'bom_ids': bom_ids,
                'total_mo': len(mo_orders),
                'total_mo_ids': mo_orders.ids,
                'total_hours': round(total_vendorbills, 2),  # Updated to show total vendor bills
                'total_profitability': round(total_invoices, 2),
                'total_sale_orders': len(sale_orders),
                'sale_orders_ids': sale_orders.ids,
                'flag': 2
            }

    @http.route('/get/expired/orders', auth='public', type='json')
    def get_expired_orders(self):
        """
        Get all sale orders that have passed their expiration date
        
        Returns:
            type: List of dictionaries containing expired sale order details
        """
        today = datetime.date.today()
        
        # Query to get expired sale orders with product details
        query = """
            SELECT 
                so.id as order_id,
                so.name, 
                rp.id as partner_id, 
                rp.name as partner_name,
                sol.id as product_id,
                sol.name as product_name,
                sol.product_uom_qty as product_qty,
                so.expired_date
            FROM 
                sale_order so
            JOIN 
                res_partner rp ON so.partner_id = rp.id
            JOIN 
                sale_order_line sol ON sol.order_id = so.id
            JOIN 
                product_product pp ON sol.product_id = pp.id
            JOIN 
                product_template pt ON pp.product_tmpl_id = pt.id
            WHERE 
                so.expired_date < %s
            ORDER BY 
                so.expired_date DESC
        """
        request._cr.execute(query, (today,))
        expired_orders = request._cr.dictfetchall()
        
        return expired_orders

    @http.route('/get/expired/invoices', auth='public', type='json')
    def get_expired_invoices(self):
        """
        Get all invoices that have passed their due date
        
        Returns:
            type: List of dictionaries containing expired invoice details
        """
        today = datetime.date.today()
        
        # Query to get expired invoices
        query = """
            SELECT 
                am.id as invoice_id,
                am.name,
                am.invoice_date_due,
                am.amount_total_in_currency_signed,
                am.payment_state
            FROM 
                account_move am
            WHERE 
                am.move_type IN ('out_invoice', 'out_refund')
                AND am.invoice_date_due < %s
                AND am.state = 'posted' 
            ORDER BY 
                am.invoice_date_due DESC
        """
        request._cr.execute(query, (today,))
        expired_invoices = request._cr.dictfetchall()
        
        return expired_invoices

    @http.route('/get/draft/manufacturing', auth='user', type='json')
    def get_draft_manufacturing(self):
        """
        Get manufacturing orders that need to be processed (Draft, Confirmed, In Progress)
        
        Returns:
            type: List of dictionaries containing manufacturing order details
        """
        try:
            # Debug: Check user permissions
            user = request.env.user
            _logger.info("Current user: %s (ID: %s)", user.name, user.id)
            _logger.info("User groups: %s", user.groups_id.mapped('name'))

            # Main query untuk mengambil manufacturing orders
            query = """
                SELECT 
                    mp.id as mo_id,
                    mp.name,
                    pt.name as product_name,
                    COALESCE(rp2.name, '') as user_name,
                    mp.create_date::text as tanggal_spk,
                    mp.product_qty,
                    COALESCE(rp.name, '') as nama_customer,
                    mp.state,
                    COALESCE(mp.origin, '') as origin 
                FROM 
                    mrp_production mp
                LEFT JOIN 
                    product_product pp ON mp.product_id = pp.id
                LEFT JOIN 
                    product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN 
                    res_users ru ON mp.user_id = ru.id
                LEFT JOIN 
                    res_partner rp ON ru.partner_id = rp.id
                LEFT JOIN
                    res_partner rp2 ON ru.partner_id = rp2.id
                LEFT JOIN
                    procurement_group pg ON mp.procurement_group_id = pg.id
                LEFT JOIN
                    sale_order so ON pg.sale_id = so.id
                WHERE 
                    mp.state IN ('draft', 'confirmed', 'progress')
                ORDER BY 
                    mp.create_date DESC
            """
            
            request._cr.execute(query)
            mo_list = request._cr.dictfetchall()
            
            return mo_list
            
        except Exception as e:
            _logger.error('Error details: %s', {
                'message': str(e),
                'traceback': traceback.format_exc(),
                'query': query
            })
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    @http.route('/get/upcoming/deliveries', auth='user', type='json')
    def get_upcoming_deliveries(self):
        """
        Get delivery orders that are approaching their deadline (within 14 days)
        
        Returns:
            type: List of dictionaries containing delivery order details
        """
        query = """
            SELECT 
                sp.id AS picking_id,
                sp.name AS reference,
                COALESCE(rp.name, '') AS partner_name,
                COALESCE(array_to_string(array_agg(pt.name), ', '), '') AS product_names,
                COALESCE(SUM(sm.product_uom_qty), 0) AS total_quantity,
                sp.date_deadline,
                sp.state
            FROM 
                stock_picking sp
            LEFT JOIN 
                res_partner rp ON sp.partner_id = rp.id
            LEFT JOIN 
                stock_move sm ON sm.picking_id = sp.id
            LEFT JOIN 
                product_product pp ON sm.product_id = pp.id
            LEFT JOIN 
                product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN 
                stock_picking_type spt ON sp.picking_type_id = spt.id
            WHERE 
                sp.state IN ('draft', 'waiting', 'confirmed', 'assigned')
                AND spt.code = 'outgoing'
            GROUP BY 
                sp.id, sp.name, rp.name, sp.date_deadline, sp.state
            ORDER BY 
                sp.date_deadline ASC
        """
        try:
            # Debug: Check user permissions
            user = request.env.user
            _logger.info("Current user: %s (ID: %s)", user.name, user.id)
            _logger.info("User groups: %s", user.groups_id.mapped('name'))

            # Debug: Check total active deliveries
            count_query = """
                SELECT COUNT(*) 
                FROM stock_picking sp
                LEFT JOIN stock_picking_type spt ON sp.picking_type_id = spt.id
                WHERE sp.state NOT IN ('done', 'cancel')
                    AND spt.code = 'outgoing'
            """
            request._cr.execute(count_query)
            total_deliveries = request._cr.fetchone()[0]
            _logger.info("Total active delivery orders: %s", total_deliveries)

            request._cr.execute(query)
            deliveries = request._cr.dictfetchall()
            
            return deliveries
            
        except Exception as e:
            _logger.error('Error details: %s', {
                'message': str(e),
                'traceback': traceback.format_exc(),
                'query': query
            })
            return {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
