from odoo import models, fields, api

# Class untuk nambahin fitur custom di purchase.order (pesanan pembelian)
class PurchaseOrderCustom(models.Model):
    """
    Class ini buat custom-in Purchase Order (PO).
    Nambahin fitur link ke SO dan MO, plus alamat vendor.
    """
    _inherit = 'purchase.order'

    # === SECTION: Link ke dokumen lain ===
    
    # Link ke Sales Order
    # Berguna buat:
    # - Tracking PO dari SO mana
    # - Gampang cek status pesanan customer
    sale_order_id = fields.Many2one(
        'sale.order', 
        string="Sales Order",
        help="Sales Order yang terkait dengan pembelian ini"
    )

    # Link ke Manufacturing Order
    # Berguna buat:
    # - Auto-isi produk dari MO
    # - Ngambil harga dari BoM
    manufacturing_order_id = fields.Many2one(
        'mrp.production', 
        string="Manufacturing Order",
        help="Manufacturing Order yang terkait dengan pembelian ini"
    )

    # Field buat nyimpen alamat lengkap vendor
    # Di-compute otomatis dari data partner
    vendor_address = fields.Text(
        string="Vendor Address", 
        compute="_compute_vendor_address",
        help="Alamat lengkap vendor"
    )

    @api.depends('partner_id')
    def _compute_vendor_address(self):
        """
        Ngambil alamat vendor otomatis dari data partner.
        
        Cara kerjanya:
        1. Ambil contact_address dari partner
        2. Kalo gak ada, isi "No Address Available"
        """
        for record in self:
            record.vendor_address = record.partner_id.contact_address or "No Address Available"

    @api.onchange('manufacturing_order_id')
    def _onchange_manufacturing_order_id(self):
        """
        Auto-isi produk dan harga pas pilih MO.
        
        Yang dikerjain:
        1. Reset dulu line yang ada
        2. Ambil produk dari MO
        3. Set harga dari BoM
        4. Update line PO
        """
        if self.manufacturing_order_id:
            # Ambil BoM dari MO
            bom = self.manufacturing_order_id.bom_id
            if not bom:
                return

            # Bersihin dulu line yang ada
            self.order_line = [(5, 0, 0)]

            # Bikin line baru dari bahan-bahan di MO
            new_lines = []
            for line in self.manufacturing_order_id.move_raw_ids:
                # Ambil harga dari BoM
                price_unit = self._get_price_from_bom(line.product_id, bom)
                
                # Siapkan data untuk line baru
                vals = {
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'price_unit': price_unit,
                    'name': line.product_id.display_name,
                    'date_planned': fields.Datetime.now(),
                    'product_uom': line.product_id.uom_po_id.id or line.product_id.uom_id.id,
                }
                new_lines.append((0, 0, vals))

            # Update order lines dengan data baru
            self.order_line = new_lines

            # Update harga tiap line
            for line in self.order_line:
                line._compute_price_unit_and_date_planned_and_name()
                line._onchange_product_id()

    def _get_price_from_bom(self, product_id, bom):
        """
        Ngambil harga dari BoM berdasarkan nama produk.
        
        Cara kerjanya:
        Cek nama produk, terus ambil harga yang sesuai dari BoM.
        Misal:
        - Kertas Cover -> ambil hrg_kertas_cover
        - Kertas Isi -> ambil hrg_kertas_isi
        dst.
        """
        if not product_id or not bom:
            return 0

        # Mapping nama produk ke field harga di BoM
        price_field_mapping = {
            "Kertas Cover": "hrg_kertas_cover",
            "Kertas Isi": "hrg_kertas_isi",
            "Plate Cover": "hrg_plate_cover",
            "Plate Isi": "hrg_plate_isi",
            "Box": "hrg_box",
        }

        # Cari field harga yang sesuai dengan nama produk
        for keyword, field_name in price_field_mapping.items():
            if keyword in product_id.name:
                return getattr(bom, field_name, 0)

        return 0

    # def _prepare_picking(self):
    #     res = super()._prepare_picking()
    #     if self.manufacturing_order_id:
    #         res['manufacturing_order_id'] = self.manufacturing_order_id.id
    #     return res


class PurchaseOrderLineCustom(models.Model):
    """
    Class ini buat custom-in Purchase Order Line.
    Tujuannya: mastiin harga di PO line selalu diambil dari BoM
    """
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'order_id.manufacturing_order_id')
    def _onchange_product_id(self):
        """
        Update harga otomatis pas:
        - Ganti produk di line PO
        - Ganti MO di header PO
        
        Tujuannya: Mastiin harga selalu dari BoM
        """
        if self.product_id and self.order_id.manufacturing_order_id:
            bom = self.order_id.manufacturing_order_id.bom_id
            self.price_unit = self.order_id._get_price_from_bom(self.product_id, bom)
            # Pake write biar UI-nya ke-update
            self.write({'price_unit': self.price_unit})

    @api.model
    def default_get(self, fields):
        """
        Set nilai default pas bikin line PO baru.
        
        Yang penting: Set harga dari BoM kalo ada MO-nya
        """
        res = super(PurchaseOrderLineCustom, self).default_get(fields)
        # Cek kalo ada PO ID di context
        if self.env.context.get('default_order_id'):
            order = self.env['purchase.order'].browse(self.env.context['default_order_id'])
            if order.manufacturing_order_id:
                bom = order.manufacturing_order_id.bom_id
                res['price_unit'] = order._get_price_from_bom(res.get('product_id'), bom)
        return res

    @api.onchange('order_id.manufacturing_order_id')
    def _onchange_order_id_manufacturing_order_id(self):
        """
        Update harga pas MO di header PO diganti.
        Mirip kayak _onchange_product_id, tapi khusus buat perubahan MO.
        """
        if self.order_id.manufacturing_order_id:
            bom = self.order_id.manufacturing_order_id.bom_id
            self.price_unit = self.order_id._get_price_from_bom(self.product_id, bom)

    @api.model
    def create(self, vals):
        """
        Override fungsi create bawaan Odoo.
        Tujuannya: mastiin harga dari BoM kepake pas bikin record baru.
        Ini penting karena kadang default vendor price bisa ngeganti harga dari BoM.
        """
        record = super(PurchaseOrderLineCustom, self).create(vals)
        if record.product_id and record.order_id.manufacturing_order_id:
            bom = record.order_id.manufacturing_order_id.bom_id
            record.price_unit = record.order_id._get_price_from_bom(record.product_id, bom)
        return record

    def write(self, vals):
        """
        Override fungsi write bawaan Odoo.
        Mirip kayak create, tapi ini buat update record yang udah ada.
        Ngecek kalo ada perubahan di product_id atau order_id.
        """
        res = super(PurchaseOrderLineCustom, self).write(vals)
        for line in self:
            if 'product_id' in vals or 'order_id' in vals:
                if line.product_id and line.order_id.manufacturing_order_id:
                    bom = line.order_id.manufacturing_order_id.bom_id
                    line.price_unit = line.order_id._get_price_from_bom(line.product_id, bom)
        return res

    @api.onchange('product_uom')
    def _onchange_product_uom(self):
        """
        Fungsi ini jalan pas satuan (UoM) produk diganti.
        Ada 2 tugas:
        1. Ngecek & benerin rounding UoM kalo ga valid
        2. Update harga dari BoM (karena kadang harga bisa berubah pas ganti satuan)
        """
        if self.product_uom:
            # Validasi rounding UoM
            if not self.product_uom.rounding or self.product_uom.rounding <= 0:
                self.product_uom.rounding = 0.01  # Default ke 0.01 kalo ga diset

            # Update harga dari BoM
            if self.order_id.manufacturing_order_id:
                bom = self.order_id.manufacturing_order_id.bom_id
                if bom:
                    self.price_unit = self.order_id._get_price_from_bom(self.product_id, bom)

            # Log buat debugging
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info(f"UoM changed: {self.product_uom.name}, Price Unit: {self.price_unit}")

    @api.depends('product_qty', 'product_uom', 'company_id', 'order_id.partner_id', 'order_id.manufacturing_order_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        """
        Override fungsi compute bawaan Odoo.
        Ini dipanggil pas ada perubahan di field-field yang di @api.depends.
        Mastiin harga dari BoM tetep kepake, ga ke-override sama logic harga default.
        """
        super()._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if line.order_id.manufacturing_order_id and line.product_id:
                bom = line.order_id.manufacturing_order_id.bom_id
                if bom:
                    price = line.order_id._get_price_from_bom(line.product_id, bom)
                    if price > 0:
                        line.price_unit = price

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     """Override untuk menambahkan pengisian lot_ids"""
    #     res = super(PurchaseOrderLineCustom, self)._onchange_product_id()
        
    #     # Tambahkan lot dari MO jika ada
    #     if self.order_id.manufacturing_order_id and self.order_id.manufacturing_order_id.lot_producing_id:
    #         self.lot_ids = [(4, self.order_id.manufacturing_order_id.lot_producing_id.id)]
        
    #     return res

    # def _prepare_stock_moves(self, picking):
    #     """Override untuk memastikan lot_ids terbawa ke stock moves"""
    #     res = super(PurchaseOrderLineCustom, self)._prepare_stock_moves(picking)
        
    #     # Tambahkan lot_ids ke stock moves jika ada
    #     if self.order_id.manufacturing_order_id and self.order_id.manufacturing_order_id.lot_producing_id:
    #         for move_vals in res:
    #             move_vals['lot_ids'] = [(4, self.order_id.manufacturing_order_id.lot_producing_id.id)]
        
    #     return res





