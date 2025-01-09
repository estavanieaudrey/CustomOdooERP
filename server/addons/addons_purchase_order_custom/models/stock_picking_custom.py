from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockPickingCustom(models.Model):
    _inherit = 'stock.picking'

    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        help="Select a Manufacturing Order to automatically populate Serial Numbers."
    )

    @api.onchange('manufacturing_order_id')
    def _onchange_manufacturing_order_id(self):
        """
        Automatically populate Serial Numbers (lot_ids) in the stock move lines
        when a Manufacturing Order is selected.
        """
        if self.manufacturing_order_id:
            mo = self.manufacturing_order_id
            _logger.info(f"Selected Manufacturing Order: {mo.name}")

            for move in self.move_ids_without_package:
                # Find the lot/serial numbers from the MO based on the product
                matching_lots = mo.finished_move_line_ids.filtered(
                    lambda l: l.product_id == move.product_id
                )
                if matching_lots:
                    try:
                        lot_ids = matching_lots.mapped('lot_producing_id')
                        if lot_ids:
                            move.move_line_ids.write({'lot_id': lot_ids[0].id})
                    except KeyError:
                        _logger.error(
                            f"'lot_producing_id' is missing in finished_move_line_ids for product {move.product_id.name}.")
                else:
                    _logger.warning(f"No matching lots found for product {move.product_id.name} in MO {mo.name}.")


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
