from odoo import models, fields, api

class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    price_satuan = fields.Float(string="Price Satuan", help="Harga per satuan item")

    @api.onchange('price_satuan', 'product_qty')
    def _onchange_price_satuan_or_quantity(self):
        for line in self:
            if line.price_satuan and line.product_qty:
                line.price_unit = line.price_satuan * line.product_qty
