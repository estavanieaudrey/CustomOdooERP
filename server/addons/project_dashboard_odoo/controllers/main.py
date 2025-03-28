from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class ProjectDashboard(http.Controller):
    @http.route('/manufacturing/waste/comparison', type='json', auth='user')
    def get_manufacturing_waste_comparison(self, **kw):
        """
        Mengambil data perbandingan waste (surplus_qty) antara buku A4 dan B5
        berdasarkan product_id dari manufacturing orders.
        """
        try:
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

            # Cari MO yang sudah selesai dan punya surplus
            mos = request.env['mrp.production'].search([
                ('state', '=', 'done'),
                ('surplus_qty', '>', 0.0)
            ])

            _logger.info(f"Total MOs found: {len(mos)}")

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

            _logger.info(f"Final result: {result}")
            return result

        except Exception as e:
            _logger.error(f"Error in waste comparison: {str(e)}")
            return {
                'labels': ['A4', 'B5'],
                'waste': [0.0, 0.0],
                'color': ['#BE1B4B', '#1FF15B'],
                'counts': [0, 0]
            } 