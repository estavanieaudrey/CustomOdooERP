from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'

    # PASAL 1: Ruang Lingkup Perjanjian
    ruang_lingkup = fields.Text(string="Ruang Lingkup Perjanjian")

    # PASAL 2: Detail Produk
    # detail_ukuran = fields.Selection(related="bom_id.ukuran_buku", string="Ukuran Buku", readonly=True)
    detail_isi = fields.Char(string="Isi", compute="_compute_detail_isi_cover", store=True)
    detail_cover = fields.Char(string="Cover", compute="_compute_detail_isi_cover", store=True)
    detail_design = fields.Char(string="Design")
    detail_jilid = fields.Selection([
        ('jahit_kawat', 'Jahit Kawat'),
        ('lem', 'Lem')
    ], string="Jilid")
    detail_packing = fields.Char(string="Packing", compute="_compute_detail_packing", readonly=True)
    detail_quantity = fields.Float(related="bom_id.qty_buku", string="Quantity Buku", readonly=True)

    # PASAL 3: Harga, Down Payment, dan Rekening Transfer
    price_unit = fields.Float(related="order_line.price_unit", string="Unit Price", readonly=True)
    total_amount = fields.Monetary(related="amount_total", string="Total Harga", readonly=True)
    down_payment_yes_no = fields.Boolean(string="Down Payment (Yes/No)")
    down_payment_percentage = fields.Float(string="Down Payment (%)")
    down_payment_nominal = fields.Float(string="Down Payment (Nominal)", compute="_compute_down_payment_nominal",
                                        store=True)
    transfer_rekening_name = fields.Char(string="Nama Rekening")
    transfer_rekening_bank = fields.Char(string="Bank")
    transfer_rekening_number = fields.Char(string="Nomor Rekening")
    transfer_rekening_branch = fields.Char(string="Cabang")

    # PASAL 4: Expired Date dan Tanda Tangan
    expired_date = fields.Date(related="validity_date", string="Expired Date", readonly=True)
    customer_signature = fields.Binary(string="Tanda Tangan", attachment=True)

    # Field untuk memilih BoM
    bom_id = fields.Many2one('mrp.bom', string="Bill of Materials", help="Pilih BoM untuk mengambil data HPP.")
    # Field untuk data perjanjian
    ukuran_buku = fields.Selection(related="bom_id.ukuran_buku", string="Ukuran Buku", readonly=True)
    jenis_cetakan_isi = fields.Selection(related="bom_id.jenis_cetakan_isi", string="Jenis Cetakan Isi", readonly=True)
    jenis_cetakan_cover = fields.Selection(related="bom_id.jenis_cetakan_cover", string="Jenis Cetakan Cover", readonly=True)
    jmlh_halaman_buku = fields.Integer(related="bom_id.jmlh_halaman_buku", string="Jumlah Halaman Buku", readonly=True)
    jasa_jilid = fields.Float(related="bom_id.jasa_jilid", string="Biaya Jilid", readonly=True)
    isi_box = fields.Float(related="bom_id.isi_box", string="Isi Box (Buku/Box)", readonly=True)
    qty_buku = fields.Float(related="bom_id.qty_buku", string="Quantity Buku", readonly=True)
    hpp_per_unit = fields.Float(related="bom_id.hpp_per_unit", string="Harga Satuan", readonly=True)
    hpp_total = fields.Float(related="bom_id.hpp_total", string="Harga Total", readonly=True)
    ppn = fields.Float(related="bom_id.ppn", string="PPn", readonly=True)

    @api.depends('bom_id.bom_line_ids')
    def _compute_detail_isi_cover(self):
        """
        Ambil produk untuk Isi dan Cover berdasarkan BoM.
        """
        for record in self:
            if record.bom_id:
                # Ambil produk isi berdasarkan default_code
                isi_lines = record.bom_id.bom_line_ids.filtered(
                    lambda l: l.product_id.default_code == "KERTAS_ISI"
                )
                record.detail_isi = ", ".join(isi_lines.mapped('product_id.name')) if isi_lines else "Tidak Ada"

                # Ambil produk cover berdasarkan default_code
                cover_lines = record.bom_id.bom_line_ids.filtered(
                    lambda l: l.product_id.default_code == "KERTAS_COVER"
                )
                record.detail_cover = ", ".join(cover_lines.mapped('product_id.name')) if cover_lines else "Tidak Ada"
            else:
                record.detail_isi = "Tidak Ada"
                record.detail_cover = "Tidak Ada"

    @api.depends('bom_id.isi_box')
    def _compute_detail_packing(self):
        """Kombinasikan isi_box dengan '/box'."""
        for record in self:
            if record.bom_id.isi_box:
                record.detail_packing = f"{record.bom_id.isi_box} /box"

    @api.depends('down_payment_percentage', 'hpp_total')
    def _compute_down_payment_nominal(self):
        """Hitung nominal Down Payment berdasarkan persentase."""
        for record in self:
            if record.down_payment_yes_no and record.down_payment_percentage:
                record.down_payment_nominal = (record.hpp_total * record.down_payment_percentage) / 100
            else:
                record.down_payment_nominal = 0.0

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """
        Ketika BoM dipilih, tambahkan data ke Order Lines.
        """
        if self.bom_id:
            # Kosongkan Order Lines sebelumnya
            self.order_line = [(5, 0, 0)]

            # Tambahkan produk berdasarkan BoM
            product = self.bom_id.product_tmpl_id.product_variant_id
            if product:
                self.order_line = [(0, 0, {
                    'product_id': product.id, #produk terkait BoM
                    'product_uom_qty': self.bom_id.qty_buku, #Jumlah produk atribut: qty_buku
                    'price_unit': self.bom_id.hpp_per_unit, #Harga satuan
                    'name': product.name, #Nama produk
                    'tax_id': [(6, 0, [])],  # Set pajak menjadi kosong
                })]

    # Field tambahan untuk informasi draft
    draft_perjanjian = fields.Binary(string="Draft Perjanjian PDF")
    draft_perjanjian_name = fields.Char(string="Nama File")
    is_signed = fields.Boolean(string="Telah Ditandatangani", default=False)
    signature_date = fields.Date(string="Tanggal Tanda Tangan")

    def action_generate_pdf(self):
        """
        Generate the draft agreement PDF.
        """
        return self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian').report_action(self)

    def action_convert_to_sales_order(self):
        """
        Convert draft quotation to confirmed sales order after validating the signature.
        """
        if not self.is_signed:
            raise ValidationError("Draft perjanjian belum ditandatangani!")
        self.action_confirm()  # Memanfaatkan metode bawaan Odoo untuk konfirmasi SO.
