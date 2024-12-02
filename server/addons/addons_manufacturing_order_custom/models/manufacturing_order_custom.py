from odoo import models, fields, api


class MrpProductionCustom(models.Model):
    _inherit = 'mrp.production'

    # Link ke Sale Order
    sale_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Link to the related Sale Order"
    )
    # Link ke Bill Of Material
    bom_id = fields.Many2one(
        'mrp.bom',
        string="Bill of Materials",
        help="Pilih BoM untuk mengambil data HPP."
    )

    # Fields yang dihitung dari Sale Order
    nama_customer = fields.Char(
        string="Nama Customer",
        compute="_compute_fields_from_sale_order",
        store=True
    )
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

    # Field tambahan untuk SPK
    tanggal_spk = fields.Date(string="Tanggal SPK", default=fields.Date.context_today)
    item_product = fields.Char(string="Item Product")
    waktu_pengiriman_pertama = fields.Datetime(string="Waktu Pengiriman Pertama")

    # Field tambahan
    jumlah_halaman = fields.Integer(
        string="Jumlah Halaman",
        compute="_compute_fields_from_bom",
        store=True
    )
    ukuran_produk_jadi = fields.Selection(
        [('a4', 'A4 (21 x 29.7 cm)'), ('b5', 'B5 (17.6 x 25 cm)')],
        string="Ukuran Produk Jadi",
        compute="_compute_fields_from_bom",
        store=True
    )
    total_produk = fields.Float(
        string="Total Produk",
        compute="_compute_fields_from_bom",
        store=True
    )

    # Spesifikasi Teknis - Bahan Cover
    ukuran_bahan_kertas = fields.Char(
        string="Ukuran Bahan Kertas",
        default="65 x 100"
    )
    ukuran_cetak = fields.Char(
        string="Ukuran Cetak"
    )
    jumlah_up_per_lembar = fields.Float(
        string="Jumlah up/Lembar"
    )
    kebutuhan_kertas_cover = fields.Float(
        string="Kebutuhan Bahan Kertas Cetak",
        compute="_compute_fields_from_bom",
        store=True
    )
    # Spesifikasi Teknis - Cetak Isi
    mesin_cetak_isi = fields.Selection(
        [('digital', 'Digital'), ('offset', 'Offset')],
        string="Mesin Cetak Isi"
    )
    bahan_kertas_isi = fields.Char(
        string="Bahan Kertas Isi",
        compute="_compute_fields_from_sale_order",
        store=True
    )
    ukuran_bahan_kertas_isi = fields.Char(
        string="Uk. Bahan Kertas Isi",
        compute="_compute_ukuran_bahan_kertas_isi",
        store=True
    )
    kebutuhan_kertas_isi = fields.Float(
        string="Kebutuhan Bahan Kertas Isi",
        compute="_compute_fields_from_bom",
        store=True
    )

    mesin_cetak_cover = fields.Selection([('digital', 'Digital'), ('offset', 'Offset')], string="Mesin Cetak Cover")
    konfigurasi_warna_cetak = fields.Char(string="Konfigurasi Warna Cetak")
    format_cetak = fields.Char(string="Format Cetak")
    jenis_cetakan_cover = fields.Selection(
        [('1_sisi', 'Cetak 1 Sisi'), ('2_sisi', 'Cetak 2 Sisi')],
        string="Jenis Cetakan Cover",
        compute="_compute_fields_from_sale_order",
        store=True
    )
    jumlah_plat = fields.Integer(
        string="Jumlah Plat",
        compute="_compute_jumlah_plat",
        store=True
    )
    finishing_cetak = fields.Selection([('laminating', 'Laminating'), ('spot_uv', 'Spot UV')], string="Finishing Cetak")

    # Others
    note = fields.Text(string="Note")
    berat_satuan_buku = fields.Float(string="Berat Satuan Buku")

    # Keterangan Lain
    toleransi_bb = fields.Float(string="Toleransi Berat Buku")
    warna_rulling = fields.Char(string="Warna Rulling")
    packing = fields.Text(string="Packing")
    ttd_pihak_percetakan = fields.Char(string="TTD Pihak Percetakan")
    ttd_pihak_customer = fields.Char(string="TTD Pihak Customer")

    # Compute Fields dari Sale Order
    @api.depends('sale_id')
    def _compute_fields_from_sale_order(self):
        """
        Mengisi field yang diambil dari Sale Order.
        """
        for production in self:
            sale_order = production.sale_id
            if sale_order:
                production.nama_customer = sale_order.partner_id.name or "Tidak Ada"
                production.nomor_pesanan = sale_order.name or "Tidak Ada"
                production.jenis_kertas_cover = sale_order.detail_cover or "Tidak Ada"
                production.jenis_uv = sale_order.jenis_uv
                production.bahan_kertas_isi = sale_order.detail_isi or "Tidak Ada"
                production.jenis_cetakan_cover = sale_order.jenis_cetakan_cover or False
            else:
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

    @api.depends('bom_id')
    def _compute_fields_from_bom(self):
        for production in self:
            bom = production.bom_id
            if bom:
                production.jumlah_halaman = bom.jmlh_halaman_buku or 0
                production.ukuran_produk_jadi = bom.ukuran_buku or False
                production.total_produk = bom.qty_buku or 0.0
                production.kebutuhan_kertas_cover = bom.kebutuhan_kertasCover or 0.0
                production.kebutuhan_kertas_isi = bom.kebutuhan_kertasIsi or 0.0
            else:
                production.jumlah_halaman = 0
                production.ukuran_produk_jadi = False
                production.total_produk = 0.0
                production.kebutuhan_kertas_cover = 0.0
                production.kebutuhan_kertas_isi = 0.0

    @api.depends('jenis_cetakan_cover')
    def _compute_jumlah_plat(self):
        """
        Menghitung jumlah plat berdasarkan jenis cetakan cover.
        """
        for record in self:
            if record.jenis_cetakan_cover == '1_sisi':
                record.jumlah_plat = 4
            elif record.jenis_cetakan_cover == '2_sisi':
                record.jumlah_plat = 8
            else:
                record.jumlah_plat = 0

    @api.depends('sale_id.order_line.product_id')
    def _compute_ukuran_bahan_kertas_isi(self):
        """
        Compute the Ukuran Bahan Kertas Isi based on the product in the linked sale order lines.
        """
        for production in self:
            # Ensure the sale order exists
            if production.sale_id and production.sale_id.order_line:
                # Get the first product in the sale order lines (assuming it's the primary product)
                product = production.sale_id.order_line[0].product_id
                if product:
                    if product.name == 'B5':
                        production.ukuran_bahan_kertas_isi = "54.6 x 73"
                    elif product.name == 'A4':
                        production.ukuran_bahan_kertas_isi = "63 x 86"
                    else:
                        production.ukuran_bahan_kertas_isi = "Tidak Diketahui"
                else:
                    production.ukuran_bahan_kertas_isi = "Tidak Diketahui"
            else:
                production.ukuran_bahan_kertas_isi = "Tidak Diketahui"

from odoo import models, fields, api


class MrpProductionCustom(models.Model):
    _inherit = 'mrp.production'

    # Link ke Sale Order
    sale_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Link to the related Sale Order"
    )
    # Link ke Bill Of Material
    bom_id = fields.Many2one(
        'mrp.bom',
        string="Bill of Materials",
        help="Pilih BoM untuk mengambil data HPP."
    )

    # Fields dari Sale Order
    nama_customer = fields.Char(
        string="Nama Customer",
        compute="_compute_fields_from_sale_order",
        store=True
    )
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

    # Field Tambahan
    tanggal_spk = fields.Date(string="Tanggal SPK", default=fields.Date.context_today)
    item_product = fields.Char(string="Item Product")
    waktu_pengiriman_pertama = fields.Datetime(string="Waktu Pengiriman Pertama")

    # Field dari BoM
    jumlah_halaman = fields.Integer(
        string="Jumlah Halaman",
        compute="_compute_fields_from_bom",
        store=True
    )
    ukuran_produk_jadi = fields.Selection(
        [('a4', 'A4 (21 x 29.7 cm)'), ('b5', 'B5 (17.6 x 25 cm)')],
        string="Ukuran Produk Jadi",
        compute="_compute_fields_from_bom",
        store=True
    )
    total_produk = fields.Float(
        string="Total Produk",
        compute="_compute_fields_from_bom",
        store=True
    )
    kebutuhan_kertas_cover = fields.Float(
        string="Kebutuhan Bahan Kertas Cover",
        compute="_compute_fields_from_bom",
        store=True
    )
    kebutuhan_kertas_isi = fields.Float(
        string="Kebutuhan Bahan Kertas Isi",
        compute="_compute_fields_from_bom",
        store=True
    )

    # Spesifikasi Teknis
    mesin_cetak_cover = fields.Selection(
        [('digital', 'Digital'), ('offset', 'Offset')],
        string="Mesin Cetak Cover"
    )
    konfigurasi_warna_cetak = fields.Char(string="Konfigurasi Warna Cetak")
    format_cetak = fields.Char(string="Format Cetak")
    jenis_cetakan_cover = fields.Selection(
        [('1_sisi', 'Cetak 1 Sisi'), ('2_sisi', 'Cetak 2 Sisi')],
        string="Jenis Cetakan Cover",
        compute="_compute_fields_from_sale_order",
        store=True
    )
    jumlah_plat = fields.Integer(
        string="Jumlah Plat",
        compute="_compute_jumlah_plat",
        store=True
    )

    finishing_cetak = fields.Selection([('laminating', 'Laminating'), ('spot_uv', 'Spot UV')], string="Finishing Cetak")

    ukuran_bahan_kertas_isi = fields.Char(
        string="Ukuran Bahan Kertas Isi",
        compute="_compute_ukuran_bahan_kertas_isi",
        store=True
    )

    # Keterangan Lain
    toleransi_bb = fields.Float(string="Toleransi Berat Buku")
    warna_rulling = fields.Char(string="Warna Rulling")
    packing = fields.Text(string="Packing")
    ttd_pihak_percetakan = fields.Char(string="TTD Pihak Percetakan")
    ttd_pihak_customer = fields.Char(string="TTD Pihak Customer")

    # 1. Compute dari Sale Order
    @api.depends('sale_id')
    def _compute_fields_from_sale_order(self):
        for production in self:
            sale_order = production.sale_id
            if sale_order:
                production.nama_customer = sale_order.partner_id.name or "Tidak Ada"
                production.nomor_pesanan = sale_order.name or "Tidak Ada"
                production.jenis_kertas_cover = sale_order.detail_cover or "Tidak Ada"
                production.jenis_uv = sale_order.jenis_uv or False
                production.jenis_cetakan_cover = sale_order.jenis_cetakan_cover or False
            else:
                production.nama_customer = "Tidak Ada"
                production.nomor_pesanan = "Tidak Ada"
                production.jenis_kertas_cover = "Tidak Ada"
                production.jenis_uv = False
                production.jenis_cetakan_cover = False

    # 2. Compute dari BoM
    @api.depends('bom_id')
    def _compute_fields_from_bom(self):
        for production in self:
            bom = production.bom_id
            if bom:
                production.jumlah_halaman = bom.jmlh_halaman_buku or 0
                production.ukuran_produk_jadi = bom.ukuran_buku or False
                production.total_produk = bom.qty_buku or 0.0
                production.kebutuhan_kertas_cover = bom.kebutuhan_kertasCover or 0.0
                production.kebutuhan_kertas_isi = bom.kebutuhan_kertasIsi or 0.0
            else:
                production.jumlah_halaman = 0
                production.ukuran_produk_jadi = False
                production.total_produk = 0.0
                production.kebutuhan_kertas_cover = 0.0
                production.kebutuhan_kertas_isi = 0.0

    # 3. Compute Jumlah Plat
    @api.depends('jenis_cetakan_cover')
    def _compute_jumlah_plat(self):
        for production in self:
            if production.jenis_cetakan_cover == '1_sisi':
                production.jumlah_plat = 4
            elif production.jenis_cetakan_cover == '2_sisi':
                production.jumlah_plat = 8
            else:
                production.jumlah_plat = 0

    # 4. Compute Ukuran Bahan Kertas Isi
    @api.depends('sale_id.order_line.product_id')
    def _compute_ukuran_bahan_kertas_isi(self):
        for production in self:
            product = production.sale_id.order_line[:1].product_id
            if product:
                if product.name == 'B5':
                    production.ukuran_bahan_kertas_isi = "54.6 x 73"
                elif product.name == 'A4':
                    production.ukuran_bahan_kertas_isi = "63 x 86"
                else:
                    production.ukuran_bahan_kertas_isi = "Tidak Diketahui"
            else:
                production.ukuran_bahan_kertas_isi = "Tidak Diketahui"

class MrpWorkorderCustom(models.Model):
    _inherit = "mrp.workorder"

    custom_qty_to_produce = fields.Float(
        string="Custom Quantity To Produce",
        compute="_compute_custom_qty_to_produce",
        store=True
    )

    @api.depends('production_id.bom_id', 'operation_id.name')
    def _compute_custom_qty_to_produce(self):
        """
        Menghitung custom_qty_to_produce berdasarkan logika yang telah dijelaskan.
        """
        for workorder in self:
            bom = workorder.production_id.bom_id
            if bom:
                # Logika berdasarkan nama operation
                if "Produksi Cetak Cover" in workorder.operation_id.name:
                    workorder.custom_qty_to_produce = bom.kebutuhan_kertasCover or 0.0
                elif "Mengirimkan ke UV Varnish" in workorder.operation_id.name:
                    workorder.custom_qty_to_produce = 0.0
                elif "Menerima Cetak Cover dari UV Varnish" in workorder.operation_id.name:
                    workorder.custom_qty_to_produce = 0.0
                elif "Produksi Cetak Isi" in workorder.operation_id.name:
                    workorder.custom_qty_to_produce = bom.kebutuhan_kertasIsi or 0.0
                elif "Join Cetak Cover dan Isi" in workorder.operation_id.name:
                    workorder.custom_qty_to_produce = 0.0
                elif "Pemotongan Akhir" in workorder.operation_id.name:
                    workorder.custom_qty_to_produce = 0.0
                elif "Packing Buku kedalam Box" in workorder.operation_id.name:
                    workorder.custom_qty_to_produce = 0.0
                else:
                    workorder.custom_qty_to_produce = 0.0
            else:
                workorder.custom_qty_to_produce = 0.0