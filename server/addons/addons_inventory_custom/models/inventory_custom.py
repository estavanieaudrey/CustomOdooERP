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

class StockMoveCustom(models.Model):
    """
    Class ini buat custom di pergerakan stok (stock.move).
    Nambahin fitur lot/serial number dan quantity control.
    """
    _inherit = 'stock.move'

    # Field buat pilih lot/serial number
    lot_id = fields.Many2one('stock.production.lot', string="Lot/Serial Number")
    
    # Field buat batasan max quantity
    # Dihitung otomatis berdasarkan stok yang ada di lot
    max_qty = fields.Float(string="Max Quantity", compute="_compute_max_qty", store=True)

    @api.depends('lot_id')
    def _compute_max_qty(self):
        """
        Ngitung max quantity yang bisa diambil dari lot yang dipilih.
        
        Cara kerjanya:
        1. Cari semua quant (record stok) yang punya lot yang sama
        2. Di lokasi yang sama
        3. Jumlahin quantitynya
        """
        for record in self:
            if record.lot_id:
                # Cari stok yang ada di lot ini
                quants = self.env['stock.quant'].search([
                    ('lot_id', '=', record.lot_id.id),
                    ('location_id', '=', record.location_id.id)
                ])
                # Total semua quantity
                record.max_qty = sum(quants.mapped('quantity'))
            else:
                record.max_qty = 0.0

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """
        Update quantity otomatis pas pilih lot.
        
        Fungsinya:
        1. Ngecek stok yang tersedia di lot
        2. Update quantity jadi sebanyak stok yang ada
        3. Update quantity_done juga (kalo ada)
        
        Ini ngebantu biar gak input quantity manual
        dan mencegah input quantity lebih dari stok
        """
        for record in self:
            if record.lot_id:
                # Cari stok yang tersedia
                quants = self.env['stock.quant'].search([
                    ('lot_id', '=', record.lot_id.id),
                    ('location_id', '=', record.location_id.id)
                ])
                available_qty = sum(quants.mapped('quantity'))
                
                # Update quantity sesuai stok
                record.product_uom_qty = available_qty
                
                # Update quantity_done juga kalo fieldnya ada
                if hasattr(record, 'quantity_done'):
                    record.quantity_done = available_qty

    # Di bawah ini ada code yang di-comment
    # Ini buat auto-isi serial number dari MO
    # Masih WIP (Work in Progress), belum jalan sempurna
    
    # @api.onchange('manufacturing_order_id')
    # def _onchange_manufacturing_order_id(self):
    #     """
    #     Auto-isi Serial Numbers dari MO yang dipilih.
    #     """
    #     ... (kode yang di-comment) ...

# Class ini juga masih WIP
# class StockMoveLineCustom(models.Model):
#     """
#     Custom untuk stock move lines.
#     Rencananya buat auto-fill lot berdasarkan MO.
#     """
#     ... (kode yang di-comment) ...
