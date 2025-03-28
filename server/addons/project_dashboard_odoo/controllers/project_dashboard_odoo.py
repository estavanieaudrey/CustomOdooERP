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
        """Summary:
            transferring data after filter 9th applied
        Args:
            kw(dict):This parameter contains the value of selection field
        Returns:
            type:dict, it contains the data for the corresponding
            filtrated transferring data to ui after filtration."""
        data = kw['data']
        # checking the employee selected or not
        if data['employee'] == 'null':
            emp_selected = [employee.id for employee in
                            request.env['hr.employee'].search([])]
        else:
            emp_selected = [int(data['employee'])]
        start_date = data['start_date']
        end_date = data['end_date']
        # checking the dates are selected or not
        if start_date != 'null' and end_date != 'null':
            start_date = datetime.datetime.strptime(start_date,
                                                    "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search(
                                    [('date_start', '>', start_date),
                                     ('date_start', '<', end_date)])]
            else:
                pro_selected = [int(data['project'])]
        elif start_date == 'null' and end_date != 'null':
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search(
                                    [('date_start', '<', end_date)])]
            else:
                pro_selected = [int(data['project'])]
        elif start_date != 'null' and end_date == 'null':
            start_date = datetime.datetime.strptime(start_date,
                                                    "%Y-%m-%d").date()
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search(
                                    [('date_start', '>', start_date)])]
            else:
                pro_selected = [int(data['project'])]
        else:
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search([])]
            else:
                pro_selected = [int(data['project'])]
        report_project = request.env['timesheets.analysis.report'].search(
            [('project_id', 'in', pro_selected),
             ('employee_id', 'in', emp_selected)])
        analytic_project = request.env['account.analytic.line'].search(
            [('project_id', 'in', pro_selected),
             ('employee_id', 'in', emp_selected)])
        margin = round(sum(report_project.mapped('margin')), 2)
        sale_orders = []
        for rec in analytic_project:
            if rec.order_id.id and rec.order_id.id not in sale_orders:
                sale_orders.append(rec.order_id.id)
        total_time = sum(analytic_project.mapped('unit_amount'))
        return {
            'total_project': pro_selected,
            'total_emp': emp_selected,
            'total_task': [rec.id for rec in request.env['project.task'].search(
                [('project_id', 'in', pro_selected)])],
            'hours_recorded': total_time,
            'list_hours_recorded': [rec.id for rec in analytic_project],
            'total_margin': margin,
            'total_so': sale_orders
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

    @http.route('/get/hours', auth='public', type='json')
    def get_hours_data(self):
        """Summary:
            when the page is loaded get the data for the hour table.
        Return:
            type:It is a dictionary variable. This dictionary contains data that
            hours table."""
        if request.env.user.has_group('project.group_project_manager'):
            query = '''SELECT sum(unit_amount) as hour_recorded FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='non_billable_project' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            hour_recorded = []
            for record in data:
                hour_recorded.append(record.get('hour_recorded'))
            query = '''SELECT sum(unit_amount) as hour_recorde FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='billable_time' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            hour_recorde = []
            for record in data:
                hour_recorde.append(record.get('hour_recorde'))
            query = '''SELECT sum(unit_amount) as billable_fix FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='billable_fixed' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            billable_fix = []
            for record in data:
                billable_fix.append(record.get('billable_fix'))
            query = '''SELECT sum(unit_amount) as non_billable FROM 
            account_analytic_line WHERE timesheet_invoice_type='non_billable' 
            '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            non_billable = []
            for record in data:
                non_billable.append(record.get('non_billable'))
            query = '''SELECT sum(unit_amount) as total_hr FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='non_billable_project' or
            timesheet_invoice_type='billable_time' or 
            timesheet_invoice_type='billable_fixed' or 
            timesheet_invoice_type='non_billable' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            total_hr = []
            for record in data:
                total_hr.append(record.get('total_hr'))
            return {
                'hour_recorded': hour_recorded,
                'hour_recorde': hour_recorde,
                'billable_fix': billable_fix,
                'non_billable': non_billable,
                'total_hr': total_hr,
            }
        else:
            all_project = request.env['project.project'].search(
                [('user_id', '=', request.env.uid)]).ids
            analytic_project = request.env['account.analytic.line'].search(
                [('project_id', 'in', all_project)])
            all_hour_recorded = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'non_billable_project')
            all_hour_recorde = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'billable_time')
            all_billable_fix = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'billable_fixed')
            all_non_billable = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'non_billable')
            hour_recorded = [sum(all_hour_recorded.mapped('unit_amount'))]
            hour_recorde = [sum(all_hour_recorde.mapped('unit_amount'))]
            billable_fix = [sum(all_billable_fix.mapped('unit_amount'))]
            non_billable = [sum(all_non_billable.mapped('unit_amount'))]
            total_hr = [
                sum(hour_recorded + hour_recorde + billable_fix + non_billable)]
            return {
                'hour_recorded': hour_recorded,
                'hour_recorde': hour_recorde,
                'billable_fix': billable_fix,
                'non_billable': non_billable,
                'total_hr': total_hr,
            }

    @http.route('/get/task/data', auth='public', type='json')
    def get_task_data(self):
        """
        Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data
            that affecting project task table."""
        if request.env.user.has_group('project.group_project_manager'):
            request._cr.execute('''select project_task.name as task_name, 
            project_task.id,
            pro.name as project_name from project_task
            Inner join project_project as pro on project_task.project_id 
            = pro.id ORDER BY project_name ASC''')
            data = request._cr.fetchall()
            project_name = []
            for rec in data:
                project_name.append(list(rec))
            return {
                'project': project_name
            }
        else:
            all_project = request.env['project.project'].search(
                [('user_id', '=', request.env.uid)]).ids
            all_tasks = request.env['project.task'].search(
                [('project_id', 'in', all_project)])
            task_project = [[task.name, task.project_id.name, task.id] for task
                            in
                            all_tasks]
            return {
                'project': task_project
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
                    COALESCE(so.name, '') as source_doc
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
