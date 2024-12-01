from odoo import models, fields, api


class MrpProductionCustom(models.Model):
    _inherit = 'mrp.production'

    # Link ke Sale Order
    sale_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Link to the related Sale Order"
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

    # Field tambahan
    jumlah_halaman = fields.Integer(
        string="Jumlah Halaman",
        compute="_compute_sale_order_fields",
        store=True
    )
    ukuran_produk_jadi = fields.Selection(
        [('a4', 'A4 (21 x 29.7 cm)'), ('b5', 'B5 (17.6 x 25 cm)')],
        string="Ukuran Produk Jadi",
        compute="_compute_sale_order_fields",
        store=True
    )
    total_produk = fields.Float(
        string="Total Produk",
        compute="_compute_sale_order_fields",
        store=True
    )

    # Field tambahan untuk SPK
    tanggal_spk = fields.Date(string="Tanggal SPK", default=fields.Date.context_today)
    item_product = fields.Char(string="Item Product")
    waktu_pengiriman_pertama = fields.Datetime(string="Waktu Pengiriman Pertama")

    # Field Spesifikasi Teknis
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

    # Compute Fields dari Sale Order
    @api.depends('sale_id')
    def _compute_fields_from_sale_order(self):
        """
        Mengisi field yang diambil dari Sale Order.
        """
        for production in self:
            sale_order = production.sale_id
            if sale_order:
                production.jenis_kertas_cover = sale_order.detail_cover or "Tidak Ada"
                production.jenis_uv = sale_order.jenis_uv
                production.nama_customer = sale_order.partner_id.name or "Tidak Ada"
                production.nomor_pesanan = sale_order.name or "Tidak Ada"
                production.jenis_cetakan_cover = sale_order.jenis_cetakan_cover or False
            else:
                production.jenis_kertas_cover = "Tidak Ada"
                production.jenis_uv = False
                production.nama_customer = "Tidak Ada"
                production.nomor_pesanan = "Tidak Ada"
                production.jenis_cetakan_cover = False

    @api.depends('sale_id')
    def _compute_sale_order_fields(self):
        """
        Mengisi field jumlah halaman, ukuran produk jadi, dan total produk.
        """
        for production in self:
            sale_order = production.sale_id
            if sale_order:
                production.jumlah_halaman = sale_order.jmlh_halaman_buku or 0
                production.ukuran_produk_jadi = sale_order.ukuran_buku or False
                production.total_produk = sale_order.qty_buku or 0.0
            else:
                production.jumlah_halaman = 0
                production.ukuran_produk_jadi = False
                production.total_produk = 0.0

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
