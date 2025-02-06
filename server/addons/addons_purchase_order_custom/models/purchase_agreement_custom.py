from odoo import models, fields, api

# Class untuk nambahin fitur custom di purchase.requisition.line (detail perjanjian pembelian)
class PurchaseRequisitionLine(models.Model):
    """
    Class ini buat custom-in detail Purchase Agreement (PA).
    Nambahin fitur hitung harga per satuan di PA lines.
    """
    _inherit = 'purchase.requisition.line'

    # Field buat nyimpen total harga
    price_total = fields.Float(
        string="Price Total", 
        help="Total harga item (quantity × harga satuan)",
        compute='_compute_price_total',
        store=True
    )

    @api.depends('price_unit', 'product_qty')
    def _compute_price_total(self):
        """
        Menghitung total harga otomatis berdasarkan:
        - Harga satuan (price_unit) yang diinput manual
        - Quantity (product_qty)
        
        Rumus:
        Total harga = harga satuan × quantity
        
        Contoh:
        - Harga satuan 10.000/kg
        - Quantity 5 kg
        - Total = 50.000
        """
        for line in self:
            line.price_total = line.price_unit * line.product_qty

class PurchaseRequisition(models.Model):
    """
    Class ini buat custom-in Purchase Agreement.
    Nambahin fitur sinkronisasi dengan BoM.
    """
    _inherit = 'purchase.requisition'

    # Link ke Bill of Materials
    # Dipake buat ngambil quantity dari BoM
    bom_id = fields.Many2one(
        'mrp.bom', 
        string="Bill of Materials",
        help="Pilih BoM untuk sinkronisasi quantity produk"
    )

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """
        Update quantity di PA lines otomatis pas pilih BoM.
        
        Cara kerjanya:
        1. Ambil semua komponen dari BoM yang dipilih
        2. Cari produk yang sama di PA lines
        3. Update quantity sesuai BoM
        
        Ini berguna buat:
        - Gak perlu input quantity manual
        - Quantity pasti sesuai BoM
        - Ngurangin kesalahan input
        """
        if self.bom_id:
            # Ambil semua komponen dari BoM
            bom_lines = self.bom_id.bom_line_ids
            
            for line in self.line_ids:
                # Cari produk yang sama di BoM
                bom_line = bom_lines.filtered(
                    lambda l: l.product_id == line.product_id
                )
                # Kalo ketemu, update quantity
                if bom_line:
                    line.product_qty = bom_line.product_qty
