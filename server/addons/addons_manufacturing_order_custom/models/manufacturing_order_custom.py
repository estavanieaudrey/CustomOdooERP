# Import library yang dibutuhin
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

# Class untuk nambahin fitur custom di manufacturing order
class MrpProductionCustom(models.Model):
    """
    Class ini buat custom-in Manufacturing Order (MO).
    Nambahin fitur khusus buat produksi percetakan.
    """
    _inherit = 'mrp.production'  # Inherit dari mrp.production bawaan Odoo
    
    # === Fields untuk tracking hasil produksi per step ===

    # Link ke Sale Order - biar tau ini MO untuk SO yang mana
    sale_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Link to the related Sale Order"
    )
    
    # Link ke sale id dan mo id
    @api.depends('sale_id')
    def _compute_sale_order_fields(self):
        for production in self:
            production.sale_id.mo_id = production.id
            
    
    # Link ke Bill Of Material - buat ngambil data HPP
    bom_id = fields.Many2one(
        'mrp.bom',
        string="Bill of Materials",
        help="Pilih BoM untuk mengambil data HPP."
    )

    # === SECTION: Fields untuk info dasar MO ===
    
    # Field buat nyimpen nama customer
    nama_customer = fields.Char(
        string="Nama Customer",
        compute="_compute_fields_from_sale_order",  # Dihitung otomatis dari SO
        store=True  # Disimpen di database biar gak perlu ngitung ulang
    )
    
    # Nomor pesanan dari SO
    nomor_pesanan = fields.Char(
        string="Nomor Pesanan",
        compute="_compute_fields_from_sale_order",
        store=True
    )
    jenis_kertas_cover = fields.Char(
        string="Jenis Kertas Cover",
        compute="_compute_fields_from_sale_order",
        store=True
    )
    jenis_uv = fields.Selection(
        [('glossy', 'Glossy'), ('matte', 'Matte (Doff)')],
        string="Jenis UV",
        compute="_compute_fields_from_sale_order",
        store=True
    )

    # Field Tambahan - data produksi
    tanggal_spk = fields.Date(
        string="Tanggal SPK", 
        default=fields.Date.context_today  # Default hari ini
    )
    item_product = fields.Char(string="Item Product")
    waktu_pengiriman_pertama = fields.Datetime(string="Waktu Pengiriman Pertama")

    # Field dari BoM - spesifikasi produk
    jumlah_halaman = fields.Integer(
        string="Jumlah Halaman",
        compute="_compute_fields_from_bom",  # Diambil dari BoM
        store=True
    )
    ukuran_produk_jadi = fields.Selection(
        [('a4', 'A4 (21 x 29.7 cm)'), ('b5', 'B5 (17.6 x 25 cm)')],
        string="Ukuran Produk Jadi",
        compute="_compute_fields_from_bom",  # Diambil dari BoM
        store=True
    )
    
    # Total produk yang mau dibuat
    total_produk = fields.Float(
        string="Total Produk",
        compute="_compute_fields_from_bom",  # Diambil dari BoM
        store=True
    )
    # === Spesifikasi Teknis - Bahan Cover ===
    ukuran_bahan_kertas_cover = fields.Char(
        string="Ukuran Bahan Kertas Cover",
        compute="_compute_ukuran_bahan_kertas_cover",
        store=True,
        help="Ukuran bahan kertas cover berdasarkan ukuran buku"
    )

    # Ukuran hasil cetakan
    ukuran_cetak = fields.Char(
        string="Ukuran Cetak"  # Ukuran hasil cetakan
    )
    
    # Berapa banyak cover yang bisa dicetak per lembar
    jumlah_up_per_lembar = fields.Float(
        string="Jumlah up/Lembar"  # Misal: 1 lembar bisa 4 cover
    )
    
    # Berapa banyak kertas cover yang dibutuhin
    kebutuhan_kertas_cover = fields.Float(
        string="Kebutuhan Bahan Kertas Cetak",
        compute="_compute_fields_from_bom",  # Dihitung dari BoM
        store=True
    )

    # === SECTION: Fields untuk spesifikasi cetak isi ===
    
    # Pilihan mesin cetak buat isi buku
    mesin_cetak_isi = fields.Selection([
        ('digital', 'Digital'),   # Pake mesin digital printing (buat qty kecil)
        ('offset', 'Offset')      # Pake mesin offset (buat qty besar)
    ], string="Mesin Cetak Isi")
    
    bahan_kertas_isi = fields.Char(
        string="Bahan Kertas Isi",
        compute="_compute_fields_from_sale_order",  # Diambil dari SO
        store=True
    )
    ukuran_bahan_kertas_isi = fields.Char(
        string="Uk. Bahan Kertas Isi",
        compute="_compute_ukuran_bahan_kertas_isi",  # Commented: mungkin mau dibikin auto
        store=True
    )
    kebutuhan_kertas_isi = fields.Float(
        string="Kebutuhan Bahan Kertas Isi",
        compute="_compute_fields_from_bom",  # Dihitung dari BoM
        store=True
    )

    # Spesifikasi Teknis - Cetak Cover
    mesin_cetak_cover = fields.Selection([
        ('digital', 'Digital'),   # Pake mesin digital printing
        ('offset', 'Offset')      # Pake mesin offset
    ], string="Mesin Cetak Cover")
    
    konfigurasi_warna_cetak = fields.Char(
        string="Konfigurasi Warna Cetak"  # Misal: CMYK, 2 warna, dll
    )
    format_cetak = fields.Char(
        string="Format Cetak"  # Format cetakan yang diinginkan
    )
    jenis_cetakan_cover = fields.Selection([
        ('1_sisi', 'Cetak 1 Sisi'),
        ('2_sisi', 'Cetak 2 Sisi')
    ], string="Jenis Cetakan Cover",
        compute="_compute_fields_from_sale_order",
        store=True
    )
    jumlah_plat = fields.Float(  # Ubah dari Integer ke Float
        string="Jumlah Plat",
        compute="_compute_jumlah_plat",
        store=True,
        digits=(16, 0),  # Menentukan presisi desimal
        help="Jumlah plat yang dibutuhkan untuk mencetak cover"
    )

    # Field untuk finishing
    finishing_cetak = fields.Selection([
        ('laminating', 'Laminating'),
        ('spot_uv', 'Spot UV')
    ], string="Finishing Cetak")
    
    # Fields untuk catatan dan info tambahan
    note = fields.Text(string="Note")  # Catatan umum
    berat_satuan_buku = fields.Float(string="Berat Satuan Buku")  # Berat per buku

    # Keterangan Lain
    toleransi_bb = fields.Float(string="Toleransi Berat Buku")
    warna_rulling = fields.Char(string="Warna Rulling")
    packing = fields.Text(string="Packing")

    # Fields yang diambil dari BoM (sekarang integer)
    gramasi_kertas_isi = fields.Integer(related="bom_id.gramasi_kertas_isi", readonly=True)
    gramasi_kertas_cover = fields.Integer(related="bom_id.gramasi_kertas_cover", readonly=True)
    qty_buku = fields.Integer(related="bom_id.qty_buku", readonly=True)
    isi_box = fields.Integer(related="bom_id.isi_box", readonly=True)
    waste_percentage = fields.Integer(related="bom_id.waste_percentage", readonly=True)

    # Field yang perlu tetap float karena melibatkan perhitungan detail
    jumlah_bahan_baku = fields.Float(string="Jumlah Bahan Baku Digunakan")
    hasil_produksi_cover = fields.Float(string="Hasil Produksi Cover")
    hasil_produksi_isi = fields.Float(string="Hasil Produksi Isi")
    qty_realita_buku = fields.Float(string="Qty Realita Buku")

    # Field buat nyimpen berapa banyak barang lebihnya
    surplus_qty = fields.Float(
        string="Surplus Quantity",
        compute="_compute_surplus_qty",  # Dihitung otomatis pake function di bawah
        store=True,  # Disimpen di database biar gak perlu ngitung ulang terus
        help="Jumlah surplus yang dihasilkan dari proses produksi."
    )

    # Field to store the sum of qty_realita_buku
    qty_plus_surplus = fields.Float(
        string="Qty Plus Surplus",
        compute="_compute_qty_plus_surplus",  # Automatically calculated field
        store=True,  # Stored in the database
        help="Sum of qty_realita_buku for accurate representation."
    )

    # Field untuk nyimpen berapa buku dalam 1 box
    isi_box = fields.Integer(
        related='bom_id.isi_box', 
        string="Isi Box", 
        store=True
    )
    
    # Add lot_id_mrp field
    lot_id_mrp = fields.Char(
        string="Lot/Serial Number MRP",
        help="Lot/Serial Number yang dipilih oleh user untuk Manufacturing Order"
    )

    # === SECTION: Fungsi-fungsi compute dan onchange ===
    # 1. Compute dari Sale Order
    @api.depends('sale_id')
    def _compute_fields_from_sale_order(self):
        """
        Ngambil data dari Sale Order dan update field-field terkait.
        
        Yang diambil:
        - Nama customer
        - Nomor pesanan
        - Jenis kertas cover & isi
        - Jenis UV
        - dll
        """
        for production in self:
            # Ambil SO yang terkait
            sale_order = production.sale_id
            if sale_order:
                # Update field-field dari data SO
                production.nama_customer = sale_order.partner_id.name or "Tidak Ada"
                production.nomor_pesanan = sale_order.name or "Tidak Ada"
                production.jenis_kertas_cover = sale_order.detail_cover or "Tidak Ada"
                production.jenis_uv = sale_order.jenis_uv
                production.bahan_kertas_isi = sale_order.detail_isi or "Tidak Ada"
                production.jenis_cetakan_cover = sale_order.jenis_cetakan_cover or False
            else:
                # Kalo gak ada SO, isi default values
                production.nama_customer = "Tidak Ada"
                production.nomor_pesanan = "Tidak Ada"
                production.jenis_kertas_cover = "Tidak Ada"
                production.jenis_uv = False
                production.bahan_kertas_isi = "Tidak Ada"
                production.jenis_cetakan_cover = False

    @api.depends('sale_id')
    def _compute_sale_order_fields(self):
        """
        Mengisi field jumlah halaman, ukuran produk jadi, dan total produk.
        """
        for production in self:
            sale_order = production.sale_id
            if sale_order:
                production.ukuran_produk_jadi = sale_order.ukuran_buku or False
                production.total_produk = sale_order.qty_buku or 0.0
            else:
                production.ukuran_produk_jadi = False
                production.total_produk = 0.0

    # 2. Compute dari BoM
    @api.depends('bom_id')
    def _compute_fields_from_bom(self):
        """
        Ngambil data dari Bill of Materials dan update field-field terkait.
        
        Yang diambil:
        - Jumlah halaman
        - Ukuran produk
        - Total produk
        - Kebutuhan kertas
        """
        for production in self:
            # Ambil BoM yang terkait
            bom = production.bom_id
            if bom:
                # Update field cuma kalo masih kosong
                # Ini biar gak overwrite data yang udah diisi manual
                production.jumlah_halaman = production.jumlah_halaman or bom.jmlh_halaman_buku or 0
                production.ukuran_produk_jadi = production.ukuran_produk_jadi or bom.ukuran_buku or False
                production.total_produk = production.total_produk or bom.qty_buku or 0.0
                production.kebutuhan_kertas_cover = production.kebutuhan_kertas_cover or bom.kebutuhan_kertasCover or 0.0
                production.kebutuhan_kertas_isi = production.kebutuhan_kertas_isi or bom.kebutuhan_kertasIsi or 0.0
            else:
                # Kalo gak ada BoM, tetep pake nilai yang udah ada atau 0
                production.jumlah_halaman = production.jumlah_halaman or 0
                production.ukuran_produk_jadi = production.ukuran_produk_jadi or False
                production.total_produk = production.total_produk or 0.0
                production.kebutuhan_kertas_cover = production.kebutuhan_kertas_cover or 0.0
                production.kebutuhan_kertas_isi = production.kebutuhan_kertas_isi or 0.0

    # 3. Compute Jumlah Plat
    @api.depends('jenis_cetakan_cover')
    def _compute_jumlah_plat(self):
        """
        Ngitung jumlah plat yang dibutuhin buat cetak cover.
        
        Rumusnya gampang:
        - Cetak 1 sisi: butuh 4 plat (CMYK)
        - Cetak 2 sisi: butuh 8 plat (CMYK x 2)
        """
        for record in self:
            if record.jenis_cetakan_cover == '1_sisi':
                record.jumlah_plat = 4.0  # CMYK = 4 plat
            elif record.jenis_cetakan_cover == '2_sisi':
                record.jumlah_plat = 8.0  # CMYK x 2 = 8 plat
            else:
                record.jumlah_plat = 0.0
                
    # 4. Compute Ukuran Bahan Kertas Isi
    @api.depends('bom_id.ukuran_buku')
    def _compute_ukuran_bahan_kertas_isi(self):
        """
        Compute the Ukuran Bahan Kertas Isi based on ukuran_buku from BoM.
        
        If ukuran_buku is:
        - a4: set to "63 x 86"
        - b5: set to "54.6 x 73"
        """
        for production in self:
            if production.bom_id and production.bom_id.ukuran_buku:
                if production.bom_id.ukuran_buku == 'a4':
                    production.ukuran_bahan_kertas_isi = "63 x 86"
                elif production.bom_id.ukuran_buku == 'b5':
                    production.ukuran_bahan_kertas_isi = "54.6 x 73"
                else:
                    production.ukuran_bahan_kertas_isi = "Tidak Diketahui"
            else:
                production.ukuran_bahan_kertas_isi = "Tidak Diketahui"
                
    # 5. Compute Ukuran Bahan Kertas Cover
    @api.depends('bom_id.ukuran_buku')
    def _compute_ukuran_bahan_kertas_cover(self):
        """
        Compute ukuran bahan kertas cover based on ukuran_buku from BoM.
        
        For A4: depends on ukuran_kertas_cover selection
        For B5: always "79 x 55"
        """
        for production in self:
            if production.bom_id and production.bom_id.ukuran_buku:
                if production.bom_id.ukuran_buku == 'a4':
                    if production.bom_id.ukuran_kertas_cover == '65x100':
                        production.ukuran_bahan_kertas_cover = "65 x 100"
                    else:  # '79x109'
                        production.ukuran_bahan_kertas_cover = "79 x 109"
                elif production.bom_id.ukuran_buku == 'b5':
                    production.ukuran_bahan_kertas_cover = "79 x 55"
                else:
                    production.ukuran_bahan_kertas_cover = "Tidak Diketahui"
            else:
                production.ukuran_bahan_kertas_cover = "Tidak Diketahui"

    def action_generate_nota(self):
        """
        Generate Nota Permintaan Barang dalam bentuk PDF.
        
        Fungsinya:
        1. Ngecek dulu ada komponen yang mau diminta apa nggak
        2. Bikin data buat nota dari move_raw_ids (list barang yang dibutuhin)
        3. Return action buat nampilin PDF nota
        """
        # Cek dulu ada komponen yang mau diminta apa nggak
        if not self.move_raw_ids:
            raise UserError("Tidak ada komponen yang terkait dengan Manufacturing Order ini.")

        # Bikin data untuk nota dari move_raw_ids (list barang yang dibutuhin)
        nota_data = [{
            'product': line.product_id.name,
            'quantity': line.product_uom_qty,
            'description': line.product_id.description or 'Tidak ada deskripsi',
        } for line in self.move_raw_ids]

        # Return action buat nampilin PDF nota
        return self.env.ref(
            'addons_manufacturing_order_custom.action_report_nota_permintaan_barang'
        ).report_action(self)

    def action_generate_spk(self): #manggil template report --> render PDF
        """
        Generate Surat Perintah Kerja (SPK) dalam bentuk PDF.
        
        SPK ini isinya:
        - Detail instruksi kerja
        - Spesifikasi produk
        - Info customer
        - dll
        """
        # Langsung return action buat nampilin PDF SPK
        return self.env.ref(
            'addons_manufacturing_order_custom.action_report_surat_perjanjian_kerja'
        ).report_action(self)

    # Function buat ngitung surplus produksi
    @api.depends('workorder_ids.qty_realita_buku', 'product_qty')
    def _compute_surplus_qty(self):
        """
        Ngitung surplus produksi.
        
        Cara kerjanya:
        1. Cari work order yang tipe nya 'packing_buku'
        2. Ambil qty_realita_buku dari packing terakhir
        3. Surplus = qty aktual - qty rencana (kalo minus jadi 0)
        """
        for production in self:
            # Cari work order packing
            packing_workorder = production.workorder_ids.filtered(
                lambda w: w.work_center_step == 'packing_buku'
            )
            if packing_workorder:
                # Ambil qty aktual dari packing terakhir
                actual_qty = packing_workorder[-1].qty_realita_buku
                # Hitung surplus (aktual - rencana), kalo minus dijadiin 0
                production.surplus_qty = actual_qty - production.product_qty if actual_qty > production.product_qty else 0.0
            else:
                production.surplus_qty = 0.0
                
    # Function yang dipanggil waktu MO selesai        
    def action_done(self):
        """
        Function yang jalan pas MO selesai.
        
        Yang dikerjain:
        1. Jalanin function bawaan Odoo dulu
        2. Update qty di stock.move sesuai hasil produksi
        """
        # Panggil function bawaan Odoo
        res = super(MrpProductionCustom, self).action_done()
        
        for production in self:
            # Cari semua stock.move yang terkait
            moves = self.env['stock.move'].search([('production_id', '=', production.id)])
            
            for move in moves:
                # Ambil qty_realita_buku dari work orders packing
                work_orders = production.workorder_ids.filtered(
                    lambda w: w.work_center_step == 'packing_buku'
                )
                # Total qty_realita_buku dari semua work orders
                real_qty = sum(work_orders.mapped('qty_realita_buku'))

                # Update qty di stock.move
                move.qty_plus_surplus_instok = real_qty if real_qty > 0 else move.product_uom_qty
                
        return res

    # Override button_mark_done buat update qty sesuai surplus
    def button_mark_done(self):
        """
        Override button_mark_done bawaan Odoo.
        
        Yang dikerjain:
        1. Jalanin function bawaan dulu
        2. Update qty di SO sesuai hasil produksi + surplus
        3. Update harga per unit (jaga biar gak berubah)
        4. Update state SO jadi 'sale'
        """
        # Jalanin function bawaan dulu
        res = super(MrpProductionCustom, self).button_mark_done()
        
        # Simpen harga per unit yang lama
        unit_price = self.sale_id.order_line.price_unit
        
        # Update qty di SO pake qty_plus_surplus
        self.sale_id.order_line.product_uom_qty = self.qty_plus_surplus
        
        # Pasang lagi harga per unit yang lama
        self.sale_id.order_line.price_unit = unit_price
        
        # Update state SO jadi 'sale'
        self.sale_id.write({'state': 'sale'})
        
        return res

    
    

    # Field to store the sum of qty_realita_buku
    qty_plus_surplus = fields.Float(
        string="Qty Plus Surplus",
        compute="_compute_qty_plus_surplus",  # Automatically calculated field
        store=True,  # Stored in the database
        help="Sum of qty_realita_buku for accurate representation."
    )
    
    # Function buat ngitung qty_plus_surplus
    @api.depends('workorder_ids.qty_realita_buku')
    def _compute_qty_plus_surplus(self):
        """
        Ngitung total qty termasuk surplus dari hasil produksi.
        
        Caranya:
        1. Cari work order yang tipe nya 'packing_buku'
        2. Ambil qty_realita_buku dari packing terakhir
        3. Itu jadi qty_plus_surplus
        """
        for production in self:
            # Cari work order yang tipe nya 'packing_buku'
            packing_workorder = production.workorder_ids.filtered(
                lambda w: w.work_center_step == 'packing_buku'
            )
            if packing_workorder:
                # Ambil qty_realita_buku dari packing terakhir
                production.qty_plus_surplus = packing_workorder[-1].qty_realita_buku
            else:
                production.qty_plus_surplus = 0.0

    isi_box = fields.Integer(related='bom_id.isi_box', string="Isi Box", store=True)

    @api.onchange('lot_id_mrp')
    def _onchange_lot_id_mrp(self):
        """
        Auto-fill lot numbers when lot_id_mrp is selected
        """
        if self.lot_id_mrp:
            for line in self.move_raw_ids:
                # Find existing lot/serial number
                lot = self.env['stock.lot'].search([
                    ('name', '=', self.lot_id_mrp),
                    ('product_id', '=', line.product_id.id),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
                
                # If lot doesn't exist, create it
                if not lot:
                    lot = self.env['stock.lot'].create({
                        'name': self.lot_id_mrp,
                        'product_id': line.product_id.id,
                        'company_id': self.company_id.id,
                    })

                # Update lot_ids in move
                line.lot_ids = [(4, lot.id)]
                
                # Create or update move lines
                if line.move_line_ids:
                    for move_line in line.move_line_ids:
                        move_line.lot_id = lot.id
                        move_line.lot_name = self.lot_id_mrp
                else:
                    self.env['stock.move.line'].create({
                        'move_id': line.id,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom.id,
                        'location_id': line.location_id.id,
                        'location_dest_id': line.location_dest_id.id,
                        'production_id': self.id,
                        'lot_id': lot.id,
                        'lot_name': self.lot_id_mrp,
                        'product_uom_qty': line.product_uom_qty,
                        'company_id': self.company_id.id,
                    })
                _logger.info(f"Created/Updated lot {self.lot_id_mrp} for product {line.product_id.name}")

    def write(self, vals):
        """Override write method to handle lot_id_mrp updates"""
        result = super().write(vals)
        
        # If lot_id_mrp was updated, ensure lot_ids are updated
        if 'lot_id_mrp' in vals and vals['lot_id_mrp']:
            for production in self:
                for line in production.move_raw_ids:
                    lot = self.env['stock.lot'].search([
                        ('name', '=', production.lot_id_mrp),
                        ('product_id', '=', line.product_id.id),
                        ('company_id', '=', production.company_id.id)
                    ], limit=1)
                    
                    if not lot:
                        lot = self.env['stock.lot'].create({
                            'name': production.lot_id_mrp,
                            'product_id': line.product_id.id,
                            'company_id': production.company_id.id,
                        })

                    # Update lot_ids in move
                    line.lot_ids = [(4, lot.id)]
                    
                    # Update or create move lines
                    if line.move_line_ids:
                        for move_line in line.move_line_ids:
                            move_line.write({
                                'lot_id': lot.id,
                                'lot_name': production.lot_id_mrp
                            })
                    else:
                        self.env['stock.move.line'].create({
                            'move_id': line.id,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_uom.id,
                            'location_id': line.location_id.id,
                            'location_dest_id': line.location_dest_id.id,
                            'production_id': production.id,
                            'lot_id': lot.id,
                            'lot_name': production.lot_id_mrp,
                            'product_uom_qty': line.product_uom_qty,
                            'company_id': production.company_id.id,
                        })
                    
                    _logger.info(f"Updated lot {production.lot_id_mrp} for product {line.product_id.name} during save")
        
        return result


# untuk mengedit custom quantity di bagian work order di Manufacturing Order
class MrpWorkorderCustom(models.Model):
    """
    Class ini buat custom-in Work Order di MO.
    Nambahin fitur tracking hasil per step produksi.
    """
    _inherit = "mrp.workorder"

    # Pilihan step/tahapan produksi
    work_center_step = fields.Selection([
        ('produksi_cetak_cover', 'Produksi Cetak Cover'),
        ('mengirimkan_ke_uv_varnish', 'Mengirimkan ke UV Varnish'),
        ('menerima_dari_uv_varnish', 'Menerima Cetak Cover dari UV Varnish'),
        ('produksi_cetak_isi', 'Produksi Cetak Isi'),
        ('join_cetak_cover_dan_isi', 'Join Cetak Cover dan Isi'),
        ('pemotongan_akhir', 'Pemotongan Akhir'),
        ('packing_buku', 'Packing Buku kedalam Box'),
    ], string="Work Center Step", required=True)

    # Fields buat ngatur visibility di form
    # Ini pake compute biar field muncul/ilang sesuai step yang dipilih
    jumlah_bahan_baku_visible = fields.Boolean(compute="_compute_visibility")
    hasil_produksi_cover_visible = fields.Boolean(compute="_compute_visibility")
    hasil_produksi_isi_visible = fields.Boolean(compute="_compute_visibility")
    qty_kirim_ke_uv_visible = fields.Boolean(compute="_compute_visibility")
    qty_terima_dari_uv_visible = fields.Boolean(compute="_compute_visibility")
    qty_realita_buku_visible = fields.Boolean(compute="_compute_visibility")

    # Fields untuk input hasil produksi
    jumlah_bahan_baku = fields.Float(string="Jumlah Bahan Baku Digunakan")
    hasil_produksi_cover = fields.Float(string="Hasil Produksi Cover")
    hasil_produksi_isi = fields.Float(string="Hasil Produksi Isi")
    hasil_join_cetak_isi = fields.Float(string="Hasil Join Cetak Isi")
    hasil_pemotongan_akhir = fields.Float(string="Hasil Pemotongan Akhir")
    qty_realita_buku = fields.Float(string="Qty Realita Buku")
    # qty_realita_box = fields.Float(string="Qty Realita Box") --kyknya gaperlu krn sudah ada jumlah_bahan_baku
    qty_buku_dalam_box = fields.Float(string="Qty Buku dalam 1 Box")

    # Fields buat proses UV
    qty_kirim_ke_uv = fields.Float(string="Qty Kirim ke UV")
    qty_terima_dari_uv = fields.Float(string="Qty Terima dari UV")

    # Dropdown untuk unit hasil produksi
    unit_type = fields.Selection([
        ('kg', 'Kg'),
        ('pcs', 'Pcs')
    ], string="Unit Type", default='pcs')

    # Fields buat ngitung waste/selisih produksi
    selisih_qty_buku = fields.Float(
        string="Selisih Qty Buku",
        compute="_compute_waste_difference",
        store=True
    )
    warning_message = fields.Char(
        string="Warning Message",
        readonly=True
    )

    # Add new field for notes
    catatan_per_workorder = fields.Text(
        string="Catatan Work Order",
        help="Catatan khusus untuk tahapan produksi ini"
    )

    # Add compute method to get notes for selected step in recap
    catatan_terpilih = fields.Text(
        string="Catatan Work Order Terpilih",
        compute='_compute_catatan_terpilih',
        help="Menampilkan catatan dari work center step yang dipilih"
    )
    
    # Add field for step selection in recap
    selected_step_for_notes = fields.Selection([
        ('produksi_cetak_cover', 'Produksi Cetak Cover'),
        ('mengirimkan_ke_uv_varnish', 'Mengirimkan ke UV Varnish'),
        ('menerima_dari_uv_varnish', 'Menerima Cetak Cover dari UV Varnish'),
        ('produksi_cetak_isi', 'Produksi Cetak Isi'),
        ('join_cetak_cover_dan_isi', 'Join Cetak Cover dan Isi'),
        ('pemotongan_akhir', 'Pemotongan Akhir'),
        ('packing_buku', 'Packing Buku kedalam Box'),
    ], string="Pilih Step untuk Melihat Catatan")

    @api.depends('selected_step_for_notes', 'production_id.workorder_ids.catatan_per_workorder')
    def _compute_catatan_terpilih(self):
        """
        Menampilkan catatan dari work center step yang dipilih.
        Jika tidak ada catatan, tampilkan pesan default.
        """
        for record in self:
            if record.selected_step_for_notes:
                # Find workorder with matching step
                matching_workorder = record.production_id.workorder_ids.filtered(
                    lambda w: w.work_center_step == record.selected_step_for_notes
                )
                if matching_workorder and matching_workorder.catatan_per_workorder:
                    record.catatan_terpilih = matching_workorder.catatan_per_workorder
                else:
                    record.catatan_terpilih = "Tidak ada catatan tambahan untuk proses ini"
            else:
                record.catatan_terpilih = "Silakan pilih work center step untuk melihat catatan"

    @api.depends("work_center_step")
    def _compute_visibility(self):
        """
        Ngatur visibility fields berdasarkan step yang dipilih.
        
        Contoh:
        - Step UV: cuma munculin field UV
        - Step packing: cuma munculin field qty buku
        """
        for record in self:
            step = record.work_center_step
            # Set visibility sesuai step yang dipilih
            record.jumlah_bahan_baku_visible = step in ['produksi_cetak_cover', 'produksi_cetak_isi']
            record.hasil_produksi_cover_visible = step == 'produksi_cetak_cover'
            record.hasil_produksi_isi_visible = step == 'produksi_cetak_isi'
            record.qty_kirim_ke_uv_visible = step == 'mengirimkan_ke_uv_varnish'
            record.qty_terima_dari_uv_visible = step == 'menerima_dari_uv_varnish'
            record.qty_realita_buku_visible = step == 'packing_buku'

    @api.model
    def create(self, vals):
        """
        Override create buat validasi step.
        Mastiin gak ada step yang dobel dalam satu MO.
        """
        if 'work_center_step' in vals and 'production_id' in vals:
            step = vals['work_center_step']
            production_id = vals['production_id']
            existing = self.search([
                ('work_center_step', '=', step),
                ('production_id', '=', production_id)
            ])
            if existing:
                raise ValidationError(f"Work Center Step '{step}' sudah dipilih dalam Manufacturing Order ini.")
        return super(MrpWorkorderCustom, self).create(vals)

    @api.onchange('production_id')
    def _onchange_production_id(self):
        """
        Filter opsi work_center_step berdasarkan langkah yang sudah dipilih di MO yang sama.
        """
        if self.production_id:
            # Dapatkan langkah-langkah yang sudah dipakai dalam MO ini
            used_steps = self.env['mrp.workorder'].search([
                ('production_id', '=', self.production_id.id),
                ('id', '!=', self.id)  # Kecualikan Work Order saat ini
            ]).mapped('work_center_step')

            # Jika ada langkah yang sudah dipakai, filter domain
            return {
                'domain': {
                    'work_center_step': [('id', 'not in', used_steps)]
                }
            }
            
            
    #custom biar work center tidak bisa disimpan > 1
    @api.model
    def create(self, vals):
        """
        Validasi pada saat membuat work order untuk memastikan hanya satu step yang aktif
        dalam Manufacturing Order (MO) yang sama.
        """
        if 'work_center_step' in vals and 'production_id' in vals:
            step = vals['work_center_step']
            production_id = vals['production_id']
            existing = self.search([
                ('work_center_step', '=', step),
                ('production_id', '=', production_id)
            ])
            if existing:
                raise ValidationError(f"Work Center Step '{step}' sudah dipilih dalam Manufacturing Order ini.")
        return super(MrpWorkorderCustom, self).create(vals)

    # ini juga biar work center tidak bisa disimpan > 1
    def write(self, vals):
        """
        Validasi agar step lain disembunyikan setelah disimpan, hanya dalam lingkup MO yang sama.
        """
        if 'work_center_step' in vals:
            step = vals['work_center_step']
            for record in self:
                production_id = record.production_id.id
                existing = self.search([
                    ('work_center_step', '=', step),
                    ('production_id', '=', production_id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(f"Work Center Step '{step}' sudah digunakan dalam Manufacturing Order ini.")
        return super(MrpWorkorderCustom, self).write(vals)

    @api.depends('qty_realita_buku', 'production_id.bom_id.qty_buku')
    def _compute_waste_difference(self):
        """
        Ngitung selisih antara qty aktual dan rencana.
        Plus kasih warning kalo ada kekurangan/kelebihan.
        """
        for record in self:
            expected_qty = record.production_id.bom_id.qty_buku
            if expected_qty and record.qty_realita_buku:
                # Hitung selisihnya
                record.selisih_qty_buku = record.qty_realita_buku - expected_qty

                # Kasih warning message sesuai kondisi
                if record.selisih_qty_buku < 0:
                    record.warning_message = _("Permintaan buku tidak tercukupi!")
                elif record.selisih_qty_buku > 0:
                    record.warning_message = _("Permintaan buku tercukupi!")
                else:
                    record.warning_message = _("Jumlah buku sesuai permintaan.")

    # @api.constrains('jumlah_bahan_baku', 'custom_qty_to_produce', 'work_center_step')
    # def _check_jumlah_bahan_baku(self):
    #     for record in self:
    #         if record.work_center_step in ['produksi_cetak_cover', 'produksi_cetak_isi']:
    #             if record.jumlah_bahan_baku > record.custom_qty_to_produce:
    #                 raise ValidationError(_(
    #                     'Jumlah bahan baku tidak boleh melebihi maksimal bahan baku (%s)'
    #                     % record.custom_qty_to_produce
    #                 ))

    # Field untuk nyimpen qty yang harus diproduksi
    custom_qty_to_produce = fields.Float(
        string="Custom Quantity To Produce",
        compute="_compute_custom_qty_to_produce",
        store=True,
    )

    # Override qty_remaining -> untuk maksa quantity to be produce mengikuti custom_qty_to_produce
    custom_qty_remaining = fields.Float(
        string="Custom Quantity Remaining",
        compute="_compute_qty_remaining",
        store=True
    )

    @api.depends('custom_qty_to_produce')
    def _compute_qty_remaining(self):
        """
        Update qty_remaining biar ngikutin custom_qty_to_produce
        """
        for work_order in self:
            work_order.qty_remaining = work_order.custom_qty_to_produce

    @api.depends(
        'production_id.bom_id',
        'production_id.bom_id.waste_percentage',
        'production_id.bom_id.kebutuhan_rim_isi',
        'production_id.bom_id.kebutuhan_kg_isi',
        'production_id.bom_id.kebutuhan_rim_cover',
        'production_id.bom_id.kebutuhan_kg_cover',
        'production_id.bom_id.qty_buku_plus_waste',
        'production_id.bom_id.isi_box',
        'operation_id.name',
        'work_center_step'
    )
    @api.onchange('work_center_step')
    def _onchange_work_center_step(self):
        """
        Recalculate custom_qty_to_produce when work_center_step changes.
        """
        for workorder in self:
            if workorder.work_center_step:
                workorder._compute_custom_qty_to_produce()

    @api.depends('production_id.bom_id', 'work_center_step')
    def _compute_custom_qty_to_produce(self):
        """
        Ngitung custom_qty_to_produce berdasarkan step dan data BoM.
        Tiap step punya rumus yang beda:
        - Cover: kebutuhan_rim_cover * kebutuhan_kg_cover * waste_factor
        - Isi: kebutuhan_rim_isi * kebutuhan_kg_isi * waste_factor
        - Packing: qty_buku_plus_waste / isi_box
        """
        for workorder in self:
            bom = workorder.production_id.bom_id
            if bom:
                waste_factor = 1 + (bom.waste_percentage / 100)

                if workorder.work_center_step == 'produksi_cetak_cover':
                    workorder.custom_qty_to_produce = (
                        bom.kebutuhan_rim_cover * bom.kebutuhan_kg_cover * waste_factor
                    ) or 0.0

                elif workorder.work_center_step == 'produksi_cetak_isi':
                    workorder.custom_qty_to_produce = (
                        bom.kebutuhan_rim_isi * bom.kebutuhan_kg_isi * waste_factor
                    ) or 0.0

                elif workorder.work_center_step == 'packing_buku':
                    workorder.custom_qty_to_produce = (
                        bom.qty_buku_plus_waste / bom.isi_box
                    ) or 0.0

                else:
                    workorder.custom_qty_to_produce = 0.0
            else:
                workorder.custom_qty_to_produce = 0.0

    @api.constrains('jumlah_bahan_baku', 'custom_qty_to_produce', 'work_center_step')
    def _check_jumlah_bahan_baku(self):
        """
        Validasi jumlah_bahan_baku:
        - Gak boleh lebih dari custom_qty_to_produce
        - Gak boleh kurang dari 90% custom_qty_to_produce
        """
        for record in self:
            if record.work_center_step in ['produksi_cetak_cover', 'produksi_cetak_isi', 'packing_buku']:
                if record.jumlah_bahan_baku > record.custom_qty_to_produce:
                    raise ValidationError(_(
                        f"Jumlah bahan baku yang anda input ({record.jumlah_bahan_baku}) tidak boleh LEBIH dari "
                        f"maksimal bahan baku ({record.custom_qty_to_produce})."
                    ))

                if record.jumlah_bahan_baku < (record.custom_qty_to_produce * 0.9):
                    raise ValidationError(_(
                        f"Jumlah bahan baku yang anda input ({record.jumlah_bahan_baku}) tidak boleh KURANG dari "
                        f"90% dari maksimal bahan baku ({record.custom_qty_to_produce * 0.9})."
                    ))

    @api.onchange('jumlah_bahan_baku')
    def _onchange_jumlah_bahan_baku(self):
        """
        Kasih warning kalo jumlah bahan baku gak sesuai:
        - Kelebihan: > custom_qty_to_produce
        - Kekurangan: < 90% custom_qty_to_produce
        """
        if self.work_center_step in ['produksi_cetak_cover', 'produksi_cetak_isi', 'packing_buku']:
            if self.jumlah_bahan_baku > self.custom_qty_to_produce:
                return {
                    'warning': {
                        'title': _('Invalid Input'),
                        'message': _(
                            f"Jumlah bahan baku yang anda input ({self.jumlah_bahan_baku}) tidak boleh LEBIH dari "
                            f"maksimal bahan baku ({self.custom_qty_to_produce})."
                        ),
                    }
                }

            if self.jumlah_bahan_baku < (self.custom_qty_to_produce * 0.9):
                return {
                    'warning': {
                        'title': _('Invalid Input'),
                        'message': _(
                            f"Jumlah bahan baku yang anda input ({self.jumlah_bahan_baku}) tidak boleh KURANG dari "
                            f"90% dari maksimal bahan baku ({self.custom_qty_to_produce * 0.9})."
                        ),
                    }
                }

    # Function buat update qty_producing
    @api.depends('qty_production', 'qty_produced')
    def _update_qty_producing(self, quantity=False):
        """
        Update qty_producing berdasarkan:
        - quantity yang dikasih (kalo ada)
        - qty_production - qty_produced (kalo gak ada quantity)
        """
        if not quantity:
            quantity = self.qty_production - self.qty_produced
            if self.production_id.product_id.tracking == 'serial':
                quantity = 1.0 if float_compare(quantity, 0,
                                                precision_rounding=self.production_id.product_uom_id.rounding) > 0 else 0
        # Set qty_producing
        self.qty_producing = quantity
        return quantity

    def button_start(self):
        """
        Override button start buat:
        1. Pastiin state MO sesuai
        2. Update quantity yang mau diproduksi
        """
        # Pastikan state MO sesuai sebelum memulai work order
        if self.production_id.state not in ['confirmed', 'progress']:
            self.production_id.write({'state': 'confirmed'})
            
        # Set date_start secara otomatis jika belum terisi
        if not self.date_start:
            self.date_start = fields.Datetime.now()

        # Pastikan Odoo tidak memeriksa date_finished (bukan date_end)
        if hasattr(self, 'date_finished') and not self.date_finished:
            self.date_finished = False  # Biarkan kosong tanpa validasi
        
        # Panggil method asli
        res = super().button_start()

        # Update quantity setelah work order dimulai
        self._update_qty_producing(self.qty_production - self.qty_produced)
        return res

    # Fields buat nyimpen total hasil produksi dari semua work orders
    hasil_produksi_cover_total = fields.Float(
        string="Total Hasil Produksi Cover",
        compute="_compute_aggregated_results",  # Dihitung otomatis
        store=False  # Gak perlu disimpen karena selalu dihitung ulang
    )
    qty_kirim_ke_uv_total = fields.Float(
        string="Total Kirim ke UV",
        compute="_compute_aggregated_results",
        store=False
    )
    qty_terima_dari_uv_total = fields.Float(
        string="Total Terima dari UV",
        compute="_compute_aggregated_results",
        store=False
    )
    hasil_produksi_isi_total = fields.Float(
        string="Total Hasil Produksi Isi",
        compute="_compute_aggregated_results",
        store=False
    )
    hasil_join_cetak_isi_total = fields.Float(
        string="Total Hasil Join Cetak Isi",
        compute="_compute_aggregated_results",
        store=False
    )
    hasil_pemotongan_akhir_total = fields.Float(
        string="Total Hasil Pemotongan Akhir",
        compute="_compute_aggregated_results",
        store=False
    )
    qty_realita_buku_total = fields.Float(
        string="Total Buku yang Masuk ke Dalam Box",
        compute="_compute_aggregated_results",
        store=False
    )

    @api.depends('production_id.workorder_ids')
    def _compute_aggregated_results(self):
        """
        Ngitung total hasil produksi dari semua work orders.
        Ini buat rekap hasil produksi di setiap step.
        """
        for workorder in self:
            # Ambil semua work orders dari MO yang sama
            workorders = workorder.production_id.workorder_ids
            
            # Jumlah semua hasil per step
            workorder.hasil_produksi_cover_total = sum(workorders.mapped('hasil_produksi_cover'))
            workorder.qty_kirim_ke_uv_total = sum(workorders.mapped('qty_kirim_ke_uv'))
            workorder.qty_terima_dari_uv_total = sum(workorders.mapped('qty_terima_dari_uv'))
            workorder.hasil_produksi_isi_total = sum(workorders.mapped('hasil_produksi_isi'))
            workorder.hasil_join_cetak_isi_total = sum(workorders.mapped('hasil_join_cetak_isi'))
            workorder.hasil_pemotongan_akhir_total = sum(workorders.mapped('hasil_pemotongan_akhir'))
            workorder.qty_realita_buku_total = sum(workorders.mapped('qty_realita_buku'))

    def action_generate_laporan_produksi(self):
        """
        Generate Laporan Hasil Produksi dalam bentuk PDF.
        Berisi rekap semua hasil produksi dari setiap step.
        """
        return self.env.ref(
            'addons_manufacturing_order_custom.action_report_laporan_hasil_produksi'
        ).report_action(self)


# Class untuk extend BoM Line (buat logging)
class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.model
    def create(self, vals):
        # _logger.info(f"Creating BoM Line: {vals}")
        return super(MrpBomLine, self).create(vals)

    def write(self, vals):
        # _logger.info(f"Updating BoM Line {self.id}: {vals}")
        return super(MrpBomLine, self).write(vals)


# Class untuk wizard MO (buat nanti kalo butuh)
class MrpWorkorderWizard(models.TransientModel):
    _name = 'mrp.workorder.wizard'
    _description = 'MRP Workorder Wizard'
    name = fields.Char(string="Name")

class StockMove(models.Model):
    _inherit = 'stock.move'

    # Field to select the manufacturing order
    manufacturing_order_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        help="Select the related Manufacturing Order."
    )
    
    # Field to fetch qty_plus_surplus from mrp.production
    qty_plus_surplus = fields.Float(
        string="Total Hasil Produksi",
        compute="_compute_qty_plus_surplus",
        store=True,
        readonly=True,
        help="Surplus quantity fetched from the related Manufacturing Order."
    )
    
    @api.depends('production_id.qty_plus_surplus')
    def _compute_qty_plus_surplus(self):
        """
        Compute qty_plus_surplus for stock.move based on the related mrp.production.
        """
        for move in self:
            if move.production_id:
                move.qty_plus_surplus = move.production_id.qty_plus_surplus #ambil dari MO
            else:
                move.qty_plus_surplus = 145.0 #default value


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Aggregate qty_plus_surplus from all stock.moves in this picking
    qty_plus_surplus = fields.Float(
        string="Total Hasil Produksi",
        compute="_compute_qty_plus_surplus",
        store=True,
        readonly=True,
        help="Sum of surplus quantities from all moves related to this picking."
    )

    @api.depends('manufacturing_order_id.qty_plus_surplus', 'manufacturing_order_id')
    def _compute_qty_plus_surplus(self):
        """
        Compute the total qty_plus_surplus for stock.picking by summing up related stock.moves.
        """
        for picking in self:
            picking.qty_plus_surplus = picking.manufacturing_order_id.qty_plus_surplus #ambil dari MO
            