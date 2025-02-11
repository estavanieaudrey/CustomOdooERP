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
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            if not picking_type:
                raise ValueError("Picking type not found for outgoing shipments")

            # Cek apakah sudah ada pengiriman sebelumnya
            existing_picking = self.env['stock.picking'].search([
                ('origin', '=', record.sale_order_id.name),
                ('state', 'not in', ['done', 'cancel'])
            ], limit=1)

            if existing_picking:
                # Jika ada pengiriman yang belum selesai, tampilkan itu
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Delivery Order',
                    'view_mode': 'form',
                    'res_model': 'stock.picking',
                    'res_id': existing_picking.id,
                    'target': 'current',
                }

            # Jika belum ada atau semua pengiriman sudah selesai, buat pengiriman baru
            picking = self.env['stock.picking'].create({
                'partner_id': record.customer_id.id,
                'picking_type_id': picking_type.id,
                'location_id': record.location_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': record.sale_order_id.name,
                'move_ids': [(0, 0, {
                    'name': record.product_id.name,
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.quantity,
                    'product_uom': record.product_uom_id.id,
                    'location_id': record.location_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'lot_ids': [(4, record.lot_id.id)] if record.lot_id else False,
                })],
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Delivery Order',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'target': 'current',
            }
            
    @api.model
    def get_dashboard_data(self):
        return self.search([
            ('location_id.usage', '=', 'internal'),
            ('location_id.name', 'not ilike', 'Production'),  # Exclude Production locations
            ('quantity', '>', 0)  # Only show positive quantities
        ])