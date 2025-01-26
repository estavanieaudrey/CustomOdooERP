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
    
class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    bom_id = fields.Many2one(
        'mrp.bom', 
        string="Bill of Materials",
        help="Select a Bill of Materials to sync product quantities."
    )

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """
        When BOM is selected, synchronize product quantities in requisition lines
        based on the BOM.
        """
        if self.bom_id:
            bom_lines = self.bom_id.bom_line_ids
            for line in self.line_ids:
                # Match products between BOM and requisition lines
                bom_line = bom_lines.filtered(lambda l: l.product_id == line.product_id)
                if bom_line:
                    line.product_qty = bom_line.product_qty  # Sync quantity
