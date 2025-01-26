from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

# Class untuk nambahin fitur custom di stock.picking (transfer barang)
class StockPickingCustom(models.Model):
    _inherit = 'stock.picking'

    # Field buat nyimpen nomor resi pengiriman
    resi_number = fields.Char(
        string="Nomor Resi",
        help="Nomor resi dari ekspedisi/kurir"
    )

    # Field buat nyimpen nomor kontainer (kalo pake kontainer)
    container_number = fields.Char(
        string="Nomor Kontainer",
        help="Nomor kontainer untuk pengiriman"
    )

    # Field buat nyimpen tanggal kedatangan kontainer
    container_arrival_date = fields.Date(
        string="Tanggal Kedatangan Kontainer",
        help="Perkiraan tanggal kontainer sampai"
    )
    # Link ke Manufacturing Order - buat auto-isi serial numbers
    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        help="Pilih MO buat auto-isi Serial Numbers"
    )

    @api.onchange('manufacturing_order_id')
    def _onchange_manufacturing_order_id(self):
        """
        Fungsi ini jalan pas MO dipilih/diganti.
        Tugasnya: Auto-isi Serial Numbers (lot_ids) di stock move lines
        berdasarkan data dari MO yang dipilih.
        """
        if self.manufacturing_order_id:
            mo = self.manufacturing_order_id
            _logger.info(f"Selected Manufacturing Order: {mo.name}")

            # Loop setiap produk di picking
            for move in self.move_ids_without_package:
                # Cari lot/serial numbers dari MO yang cocok sama produknya
                matching_lots = mo.finished_move_line_ids.filtered(
                    lambda l: l.product_id == move.product_id
                )
                if matching_lots:
                    try:
                        # Ambil lot_producing_id dari MO
                        lot_ids = matching_lots.mapped('lot_producing_id')
                        if lot_ids:
                            # Update lot_id di move lines
                            move.move_line_ids.write({'lot_id': lot_ids[0].id})
                    except KeyError:
                        _logger.error(
                            f"'lot_producing_id' gak ada di finished_move_line_ids untuk produk {move.product_id.name}."
                        )
                else:
                    _logger.warning(f"Gak ketemu lot yang cocok untuk produk {move.product_id.name} di MO {mo.name}.")


class StockMoveLineCustom(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('product_id', 'lot_id')
    def _onchange_product_and_lot(self):
        """
        Ensure the lot_id matches the product and is pre-filled based on the linked MO.
        """
        if self.move_id.picking_id.manufacturing_order_id:
            mo = self.move_id.picking_id.manufacturing_order_id
            matching_lots = mo.finished_move_line_ids.filtered(
                lambda l: l.product_id == self.product_id
            ).mapped('lot_producing_id')

            if matching_lots:
                self.lot_id = matching_lots[0]  # Assign the first matching lot
                _logger.info(f"Pre-filled lot {matching_lots[0].name} for product {self.product_id.name}")
