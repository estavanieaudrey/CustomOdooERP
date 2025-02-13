from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

# Class untuk nambahin fitur custom di stock.picking (transfer barang)
class StockPickingCustom(models.Model):
    """
    Class ini buat nambahin fitur di transfer barang (stock.picking).
    Nambah field kayak nomor resi, kontainer, dll.
    """
    _inherit = 'stock.picking'
    

    # Field buat nyimpen nomor resi pengiriman
    # Berguna buat:
    # - Tracking pengiriman
    # - Bukti pengiriman
    # - Referensi ke ekspedisi
    resi_number = fields.Char(
        string="Nomor Resi",
        help="Nomor resi dari ekspedisi/kurir"
    )

    # Field buat nyimpen nomor kontainer
    # Kepake kalo pengiriman pake kontainer
    # (biasanya buat ekspor atau pengiriman antar pulau)
    container_number = fields.Char(
        string="Nomor Kontainer",
        help="Nomor kontainer untuk pengiriman"
    )

    # Field buat nyimpen perkiraan tanggal kontainer sampe
    # Penting buat:
    # - Planning penerimaan barang
    # - Koordinasi dengan gudang
    container_arrival_date = fields.Date(
        string="Tanggal Kedatangan Kontainer",
        help="Perkiraan tanggal kontainer sampai"
    )

    # Link ke Manufacturing Order
    # Dipake buat auto-isi serial numbers dari MO ke transfer
    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        help="Pilih MO buat auto-isi Serial Numbers"
    )

    # Link ke Sale Order
    sale_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Link to the related Sale Order"
    )
    
    lot_producing_id = fields.Many2one(
        related='manufacturing_order_id.lot_producing_id',
        string='Lot/Serial Number Production',
        readonly=True,
    )

    # Tambahkan definisi field lot_id_stock
    lot_id_stock = fields.Char(
        string="Lot/Serial Number Stock",
        help="Lot/Serial Number yang dipilih oleh user"
    )

    @api.onchange('lot_id_stock')
    def _onchange_lot_id_stock(self):
        """
        Auto-fill lot numbers when lot_id_stock is selected
        """
        if self.lot_id_stock:
            for move in self.move_ids_without_package:
                # Find existing lot/serial number
                lot = self.env['stock.lot'].search([
                    ('name', '=', self.lot_id_stock),
                    ('product_id', '=', move.product_id.id),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
                
                # If lot doesn't exist, create it
                if not lot:
                    lot = self.env['stock.lot'].create({
                        'name': self.lot_id_stock,
                        'product_id': move.product_id.id,
                        'company_id': self.company_id.id,
                    })

                # Update lot_ids in move
                move.lot_ids = [(4, lot.id)]
                
                # Create move lines if needed
                if move.move_line_ids:
                    for move_line in move.move_line_ids:
                        move_line.lot_id = lot.id
                        move_line.lot_name = self.lot_id_stock
                else:
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'picking_id': self.id,
                        'lot_id': lot.id,
                        'lot_name': self.lot_id_stock,
                        'product_uom_qty': move.product_uom_qty,
                        'company_id': self.company_id.id,
                    })
                _logger.info(f"Created/Updated lot {self.lot_id_stock} for product {move.product_id.name}")

    def write(self, vals):
        """Override write method to handle lot_id_stock updates"""
        result = super().write(vals)
        
        # If lot_id_stock was updated, ensure lot_ids are updated
        if 'lot_id_stock' in vals and vals['lot_id_stock']:
            for picking in self:
                for move in picking.move_ids_without_package:
                    lot = self.env['stock.lot'].search([
                        ('name', '=', picking.lot_id_stock),
                        ('product_id', '=', move.product_id.id),
                        ('company_id', '=', picking.company_id.id)
                    ], limit=1)
                    
                    if not lot:
                        lot = self.env['stock.lot'].create({
                            'name': picking.lot_id_stock,
                            'product_id': move.product_id.id,
                            'company_id': picking.company_id.id,
                        })

                    # Update lot_ids in move
                    move.lot_ids = [(4, lot.id)]
                    
                    # Update or create move lines
                    if move.move_line_ids:
                        for move_line in move.move_line_ids:
                            move_line.write({
                                'lot_id': lot.id,
                                'lot_name': picking.lot_id_stock
                            })
                    else:
                        self.env['stock.move.line'].create({
                            'move_id': move.id,
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_uom.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'picking_id': picking.id,
                            'lot_id': lot.id,
                            'lot_name': picking.lot_id_stock,
                            'product_uom_qty': move.product_uom_qty,
                            'company_id': picking.company_id.id,
                        })
                    
                    _logger.info(f"Updated lot {picking.lot_id_stock} for product {move.product_id.name} during save")
        
        return result

class StockMoveCustom(models.Model):
    """
    Class ini buat custom di pergerakan stok (stock.move).
    Nambahin fitur lot/serial number dan quantity control.
    """
    _inherit = 'stock.move'

    # Link to Manufacturing Order through picking
    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        related='picking_id.manufacturing_order_id',
        store=True,
        string="Manufacturing Order"
    )

    # Field for lot selection
    lot_id = fields.Many2one(
        'stock.lot',
        string="Lot/Serial Number"
    )

    @api.onchange('picking_id.lot_id_stock')
    def _onchange_picking_lot_id_stock(self):
        """
        Auto-fill lot when lot_id_stock changes in picking
        """
        if self.picking_id.lot_id_stock:
            # Find or create lot
            lot = self.env['stock.lot'].search([
                ('name', '=', self.picking_id.lot_id_stock),
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not lot:
                lot = self.env['stock.lot'].create({
                    'name': self.picking_id.lot_id_stock,
                    'product_id': self.product_id.id,
                    'company_id': self.company_id.id,
                })
            
            # Update lot_ids using 4 command to add to many2many
            self.lot_ids = [(4, lot.id)]
            
            # Update move lines if they exist
            if self.move_line_ids:
                for move_line in self.move_line_ids:
                    move_line.lot_id = lot.id
                    move_line.lot_name = self.picking_id.lot_id_stock
            else:
                self.env['stock.move.line'].create({
                    'move_id': self.id,
                    'product_id': self.product_id.id,
                    'product_uom_id': self.product_uom.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'picking_id': self.picking_id.id,
                    'lot_id': lot.id,
                    'lot_name': self.picking_id.lot_id_stock,
                    'product_uom_qty': self.product_uom_qty,
                    'company_id': self.company_id.id,
                })
            _logger.info(f"Created/Updated lot {self.picking_id.lot_id_stock} for product {self.product_id.name}")

class StockMoveLineCustom(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('move_id.picking_id.lot_id_stock')
    def _onchange_picking_lot_id_stock(self):
        """
        Auto-fill lot and quantity when lot_id_stock changes at move line level
        """
        if self.move_id.picking_id.lot_id_stock:
            # self.lot_id = self.move_id.picking_id.lot_id_stock.id
            # self.lot_name = self.move_id.picking_id.lot_id_stock.name
            # _logger.info(f"Auto-filled lot {self.move_id.picking_id.lot_id_stock.name} for product {self.product_id.name}")
            # Find the lot record
            lot = self.env['stock.lot'].search([
                ('name', '=', self.move_id.picking_id.lot_id_stock),
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if lot:
                self.lot_id = lot.id
                self.lot_name = lot.name
                # Get the total quantity from the lot (on_hand)
                quant = self.env['stock.quant'].search([
                    ('lot_id', '=', lot.id),
                    ('location_id', '=', self.location_id.id),
                    ('product_id', '=', self.product_id.id)
                ], limit=1)
                
                if quant:
                    # self.product_uom_qty = quant.quantity
                    # _logger.info(f"Auto-filled lot {lot.name} with quantity {quant.quantity} for product {self.product_id.name}")

                    # Menggunakan quantity (on_hand) bukan reserved quantity
                    total_quantity = quant.quantity
                    self.product_uom_qty = total_quantity
                    _logger.info(f"Auto-filled lot {lot.name} with total quantity {total_quantity} for product {self.product_id.name}")
