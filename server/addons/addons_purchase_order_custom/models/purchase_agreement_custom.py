from odoo import models, fields, api
from odoo.exceptions import ValidationError

# Class untuk nambahin fitur custom di purchase.requisition.line (detail perjanjian pembelian)
class PurchaseRequisitionLine(models.Model):
    """
    Class ini buat custom-in detail Purchase Agreement (PA).
    Nambahin fitur hitung harga per satuan di PA lines.
    """
    _inherit = 'purchase.requisition.line'
    
    # Override product_qty field to set default to 1
    product_qty = fields.Float(
        string='Quantity', 
        default=1.0,
        readonly=True,
        digits='Product Unit of Measure'
    )

    # Field buat nyimpen total harga
    price_total = fields.Float(
        string="Price Total", 
        help="Total harga item (quantity × harga satuan)",
        compute='_compute_price_total',
        store=True
    )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Set quantity to 1 whenever product is changed
        """
        if self.product_id:
            self.product_qty = 1.0

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
    
    # Override user_id field to set default value and make it readonly
    user_id = fields.Many2one(
        'res.users', 
        string='Purchase Representative',
        default=lambda self: self.env.user,
        readonly=True,
        states={'draft': [('readonly', False)]},  # Only editable in draft state for admin
        tracking=True
    )
    
    # Override picking_type_id to make it readonly but still readable
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type',
        required=True,
        readonly=True,  # Always readonly
        domain=[('code', '=', 'incoming')],
        tracking=True,
        default=lambda self: self._get_default_picking_type()
    )
    
    # Link ke Bill of Materials
    # Dipake buat ngambil quantity dari BoM
    bom_id = fields.Many2one(
        'mrp.bom', 
        string="Bill of Materials",
        help="Pilih BoM untuk sinkronisasi quantity produk"
    )
    
    @api.model
    def create(self, vals):
        """
        Override create method to ensure user_id is always set
        """
        # Always set the current user if not provided
        if 'user_id' not in vals:
            vals['user_id'] = self.env.user.id
            
        return super(PurchaseRequisition, self).create(vals)
    
    def _get_default_picking_type(self):
        """Get default picking type for the current user's company"""
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return warehouse.in_type_id.id if warehouse else False

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

    def action_confirm(self):
        """
        Override action_confirm untuk validasi field mandatory sebelum konfirmasi.
        """
        for requisition in self:
            missing_fields = []

            # Validasi date_start
            if not requisition.date_start:
                missing_fields.append('Agreement Validity Date')

            # Validasi product_id di setiap line
            if not requisition.line_ids:
                raise ValidationError("Anda harus menambahkan minimal satu produk sebelum konfirmasi!")

            for line in requisition.line_ids:
                if not line.product_id:
                    missing_fields.append('Product di Purchase Agreement Lines')
                    break  # Cukup sekali saja warning untuk product yang kosong
                
            # Validasi bom_id : gabutuh sih krn sudah ada warning dari sisi quantity
            # if not requisition.bom_id:
            #     missing_fields.append('Bill of Materials')
            #
            # if missing_fields:
            #     raise ValidationError(
            #         # isi date_start, product_id, dan quantity
            #         f"Silakan isi field berikut sebelum konfirmasi: {', '.join(missing_fields)}"
            #     )

        return super(PurchaseRequisition, self).action_confirm()
