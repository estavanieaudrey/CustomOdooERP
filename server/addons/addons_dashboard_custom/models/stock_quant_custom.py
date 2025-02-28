from odoo import models, fields, api

class StockQuantCustom(models.Model):
    _inherit = 'stock.quant'
    '''
        dashboard hanya akan menampilkan:
        - Barang yang berada di lokasi internal (bukan virtual)
        - Mengecualikan lokasi produksi
        - Hanya menampilkan stok yang positif (sudah masuk gudang)
    '''

    customer_id = fields.Many2one(
        'res.partner',
        string="Customer",
        compute="_compute_customer_info",
        store=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sales Order",
        compute="_compute_customer_info",
        store=True
    )

    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        compute="_compute_customer_info",
        store=True
    )

    lot_producing_id = fields.Many2one(
        'stock.lot',
        string="Lot/Serial Number",
        related="lot_id",
        store=True
    )

    @api.depends('lot_id')
    def _compute_customer_info(self):
        for record in self:
            # Reset values
            record.manufacturing_order_id = False
            record.sale_order_id = False
            record.customer_id = False
            
            # Cari MO berdasarkan lot
            mo = self.env['mrp.production'].search([('lot_producing_id', '=', record.lot_id.id)], limit=1)
            if mo:
                record.manufacturing_order_id = mo.id
                if mo.sale_id:
                    record.sale_order_id = mo.sale_id.id
                    record.customer_id = mo.sale_id.partner_id.id
            else:
                # Jika tidak ada MO, coba cari dari move_line
                move_line = self.env['stock.move.line'].search([
                    ('lot_id', '=', record.lot_id.id),
                    ('move_id.sale_line_id', '!=', False)
                ], limit=1)
                if move_line and move_line.move_id.sale_line_id:
                    sale_line = move_line.move_id.sale_line_id
                    record.sale_order_id = sale_line.order_id.id
                    record.customer_id = sale_line.order_id.partner_id.id

    def action_create_delivery(self):
        for record in self:
            if not record.sale_order_id:
                raise ValueError("No Sales Order found for this record")

            # Cari semua pengiriman yang terkait dengan SO
            pickings = self.env['stock.picking'].search([
                ('origin', '=', record.sale_order_id.name),
                ('state', 'not in', ['cancel'])
            ])

            if not pickings:
                raise ValueError("No delivery orders found for this Sales Order")

            if len(pickings) == 1:
                # Jika hanya ada 1 pengiriman, tampilkan form view
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Delivery Order',
                    'view_mode': 'form',
                    'res_model': 'stock.picking',
                    'res_id': pickings[0].id,
                    'target': 'current',
                }
            else:
                # Jika ada lebih dari 1 pengiriman, tampilkan list view
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Delivery Orders',
                    'view_mode': 'list,form',
                    'res_model': 'stock.picking',
                    'domain': [('id', 'in', pickings.ids)],
                    'target': 'current',
                }

    # @api.model
    # def get_dashboard_data(self):
    #     # Flush any pending computations and clear caches
    #     self.env.cr.flush()
    #     self.invalidate_cache()
        
    #     # Get only internal locations first
    #     internal_locations = self.env['stock.location'].search([
    #         ('usage', '=', 'internal')
    #     ])
        
    #     return self.search([
    #         ('location_id', 'in', internal_locations.ids),
    #         ('quantity', '>', 0)  # Only show positive quantities
    #     ])