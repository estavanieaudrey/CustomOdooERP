from odoo import models, fields, api

# Class untuk nambahin fitur custom di purchase.requisition.line (detail perjanjian pembelian)
class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'
    # Field buat nyimpen harga satuan item

        # Field buat nyimpen harga satuan item
    price_satuan = fields.Float(
        string="Price Satuan", 
        help="Harga per satuan item"
    )

    @api.onchange('price_satuan', 'product_qty')
    def _onchange_price_satuan_or_quantity(self):
        """
        Fungsi ini jalan pas:
        - Harga satuan diubah
        - Quantity diubah
        Tugasnya: Update price_unit (total harga) = harga satuan * quantity
        """
        for line in self:
            if line.price_satuan and line.product_qty:
                line.price_unit = line.price_satuan * line.product_qty
