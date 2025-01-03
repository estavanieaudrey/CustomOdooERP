from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

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
    # Others
    note = fields.Text(string="Note")
    berat_satuan_buku = fields.Float(string="Berat Satuan Buku")

    # Keterangan Lain
    toleransi_bb = fields.Float(string="Toleransi Berat Buku")
    warna_rulling = fields.Char(string="Warna Rulling")
    packing = fields.Text(string="Packing")
    ttd_pihak_percetakan = fields.Char(string="TTD Pihak Percetakan")
    ttd_pihak_customer = fields.Char(string="TTD Pihak Customer")

    # 1. Compute dari Sale Order
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

    # 2. Compute dari BoM
    @api.depends('bom_id')
    def _compute_fields_from_bom(self):
        for production in self:
            bom = production.bom_id
            if bom:
                # Hanya hitung jika data kosong
                production.jumlah_halaman = production.jumlah_halaman or bom.jmlh_halaman_buku or 0
                production.ukuran_produk_jadi = production.ukuran_produk_jadi or bom.ukuran_buku or False
                production.total_produk = production.total_produk or bom.qty_buku or 0.0
                production.kebutuhan_kertas_cover = production.kebutuhan_kertas_cover or bom.kebutuhan_kertasCover or 0.0
                production.kebutuhan_kertas_isi = production.kebutuhan_kertas_isi or bom.kebutuhan_kertasIsi or 0.0
            else:
                # Jika tidak ada BoM, biarkan data tetap kosong
                production.jumlah_halaman = production.jumlah_halaman or 0
                production.ukuran_produk_jadi = production.ukuran_produk_jadi or False
                production.total_produk = production.total_produk or 0.0
                production.kebutuhan_kertas_cover = production.kebutuhan_kertas_cover or 0.0
                production.kebutuhan_kertas_isi = production.kebutuhan_kertas_isi or 0.0

    # 3. Compute Jumlah Plat
    @api.depends('jenis_cetakan_cover')
    def _compute_jumlah_plat(self):
        for record in self:
            if record.jenis_cetakan_cover == '1_sisi':
                record.jumlah_plat = 4
            elif record.jenis_cetakan_cover == '2_sisi':
                record.jumlah_plat = 8
            else:
                record.jumlah_plat = 0

    # 4. Compute Ukuran Bahan Kertas Isi
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

    def action_generate_nota(self):
        """
        Generate Nota Permintaan Barang dan tampilkan sebagai laporan PDF.
        """
        # Gunakan move_raw_ids untuk mengambil data aktual dari MO, bukan langsung dari BoM
        if not self.move_raw_ids:
            raise UserError("Tidak ada komponen yang terkait dengan Manufacturing Order ini.")

        # Buat laporan berdasarkan data komponen di move_raw_ids
        nota_data = [{
            'product': line.product_id.name,
            'quantity': line.product_uom_qty,
            'description': line.product_id.description or 'Tidak ada deskripsi',
        } for line in self.move_raw_ids]

        # Kembalikan laporan
        return self.env.ref(
            'addons_manufacturing_order_custom.action_report_nota_permintaan_barang'
        ).report_action(self)
        # return report_action

    def action_generate_spk(self):
        """
        Function buat bikin PDF dari template report yang udah dibuat.
        Simpel sih, cuma manggil template reportnya terus dirender jadi PDF.
        """
        # Manggil template report yang udah didaftarin di XML, terus langsung dirender
        return self.env.ref('addons_manufacturing_order_custom.action_report_surat_perjanjian_kerja').report_action(self)

# untuk mengedit custom quantity di bagian work order di Manufacturing Order
class MrpWorkorderCustom(models.Model):
    _inherit = "mrp.workorder"

    # Input Fields
    jumlah_bahan_baku = fields.Float(
        string="Jumlah Bahan Baku Digunakan",
        help="Input jumlah bahan baku yang digunakan pada proses ini."
    )

    # Production Output Fields
    hasil_produksi_cover = fields.Float(string="Hasil Produksi Cover")
    hasil_produksi_isi = fields.Float(string="Hasil Produksi Isi")
    hasil_join_cetak_isi = fields.Float(string="Hasil Join Cetak Isi")
    hasil_pemotongan_akhir = fields.Float(string="Hasil Pemotongan Akhir")
    qty_realita_buku = fields.Float(string="Qty Realita Buku")
    qty_realita_box = fields.Float(string="Qty Realita Box")
    qty_buku_dalam_box = fields.Float(string="Qty Buku dalam 1 Box")
    
    # UV Process Fields
    qty_kirim_ke_uv = fields.Float(string="Qty Kirim ke UV")
    qty_terima_dari_uv = fields.Float(string="Qty Terima dari UV")

    # Unit Selection for Results
    unit_type = fields.Selection([
        ('kg', 'Kg'),
        ('pcs', 'Pcs')
    ], string="Unit Type", default='pcs')

    # Waste Calculation
    selisih_qty_buku = fields.Float(
        string="Selisih Qty Buku",
        compute="_compute_waste_difference",
        store=True
    )
    warning_message = fields.Char(
        string="Warning Message", 
        readonly=True
    )

    @api.depends('qty_realita_buku', 'production_id.bom_id.qty_buku')
    def _compute_waste_difference(self):
        for record in self:
            expected_qty = record.production_id.bom_id.qty_buku
            if expected_qty and record.qty_realita_buku:
                record.selisih_qty_buku = record.qty_realita_buku - expected_qty

                if record.selisih_qty_buku < 0:
                    record.warning_message = _("Permintaan buku tidak tercukupi!")
                elif record.selisih_qty_buku > 0:
                    record.warning_message = _("Permintaan buku tercukupi!")
                else:
                    record.warning_message = _("Jumlah buku sesuai permintaan.")

    @api.constrains('jumlah_bahan_baku', 'workcenter_id')
    def _check_bahan_baku(self):
        for record in self:
            if record.workcenter_id.name in ['Produksi Cetak Cover', 'Produksi Cetak Isi']:
                if record.jumlah_bahan_baku < 0:
                    raise ValidationError(_("Jumlah bahan baku tidak boleh kurang dari 0!"))
                if record.jumlah_bahan_baku > record.production_id.bom_id.qty_buku:
                    raise ValidationError(_(
                        f"Jumlah bahan baku melebihi kebutuhan untuk {record.workcenter_id.name}!\n"
                        f"Maksimal: {record.production_id.bom_id.qty_buku}"
                    ))

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
        for work_order in self:
            work_order.qty_remaining = work_order.custom_qty_to_produce


    @api.depends(
        'production_id.bom_id',
        'production_id.bom_id.kebutuhan_rim_isi',
        'production_id.bom_id.kebutuhan_kg_isi',
        'production_id.bom_id.kebutuhan_rim_cover',
        'production_id.bom_id.kebutuhan_kg_cover',
        'operation_id.name'
    )

    def _compute_custom_qty_to_produce(self):
        """
        Menghitung custom_qty_to_produce berdasarkan kebutuhan di BoM dan operasi workorder.
        """
        for workorder in self:
            bom = workorder.production_id.bom_id
            if bom:
                waste_factor = 1 + (bom.waste_percentage / 100)

                # Identifikasi operasi dan tentukan quantity berdasarkan nama
                if "Produksi Cetak Cover" in workorder.operation_id.name:
                    # Menggunakan perhitungan kertas cover
                    custom_qty = (bom.kebutuhan_rim_cover * bom.kebutuhan_kg_cover) * waste_factor
                    workorder.custom_qty_to_produce = custom_qty or 0.0

                elif "Produksi Cetak Isi" in workorder.operation_id.name:
                    # Menggunakan perhitungan kertas isi
                    custom_qty = (bom.kebutuhan_rim_isi * bom.kebutuhan_kg_isi) * waste_factor
                    workorder.custom_qty_to_produce = custom_qty or 0.0

                elif "Packing Buku kedalam Box" in workorder.operation_id.name:
                    # Menggunakan perhitungan packing box
                    if bom.isi_box > 0:
                        custom_qty = bom.qty_buku / bom.isi_box
                    else:
                        custom_qty = 0.0
                    workorder.custom_qty_to_produce = custom_qty or 0.0

                else:
                    # Default untuk operasi lain
                    workorder.custom_qty_to_produce = 0.0
            else:
                workorder.custom_qty_to_produce = 0.0

    @api.onchange('jumlah_bahan_baku')
    def _onchange_jumlah_bahan_baku(self):
        if self.workcenter_id.name in ['Produksi Cetak Cover', 'Produksi Cetak Isi']:
            # Mengakses qty_buku melalui production_id.bom_id
            if self.jumlah_bahan_baku and self.production_id.bom_id.qty_buku:
                usage_percentage = (self.jumlah_bahan_baku / self.production_id.bom_id.qty_buku) * 100
                if usage_percentage < 80:
                    return {
                        'warning': {
                            'title': _('Peringatan Penggunaan Bahan Baku'),
                            'message': _(
                                f"Jumlah bahan baku yang diinput ({self.jumlah_bahan_baku}) "
                                f"kurang dari 80% dari kebutuhan yang dihitung ({self.production_id.bom_id.qty_buku}). "
                                f"Pastikan jumlah ini sudah benar."
                            )
                        }
                    }

    # untuk mengupdate qty_producing
    @api.depends('qty_production', 'qty_produced')
    def _update_qty_producing(self, quantity=False):
        if not quantity:
            quantity = self.qty_production - self.qty_produced
            if self.production_id.product_id.tracking == 'serial':
                quantity = 1.0 if float_compare(quantity, 0, precision_rounding=self.production_id.product_uom_id.rounding) > 0 else 0
        # Tidak menggunakan custom_qty_to_produce
        self.qty_producing = quantity
        return quantity

    def button_start(self):
        # Pastikan state MO sesuai sebelum memulai work order
        if self.production_id.state not in ['confirmed', 'progress']:
            self.production_id.write({'state': 'confirmed'})
        
        # Panggil method asli
        res = super().button_start()
        
        # Update quantity setelah work order dimulai
        self._update_qty_producing(self.qty_production - self.qty_produced)
        return res

    

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.model
    def create(self, vals):
        # _logger.info(f"Creating BoM Line: {vals}")
        return super(MrpBomLine, self).create(vals)

    def write(self, vals):
        # _logger.info(f"Updating BoM Line {self.id}: {vals}")
        return super(MrpBomLine, self).write(vals)

class MrpWorkorderWizard(models.TransientModel):
    _name = 'mrp.workorder.wizard'
    _description = 'MRP Workorder Wizard'

    name = fields.Char(string="Name")

# Add a new field to mrp.stock.move to store original quantities
class StockMove(models.Model):
    _inherit = 'stock.move'

    original_qty = fields.Float(
        string="Original Quantity",
        help="Stores the original quantity before any auto-calculations"
    )
#
# # class MrpWorkorderCustom(models.Model):
#     _inherit = 'mrp.workorder'
#
#     # Visibility Helper Fields
#     is_visible_jumlah_bahan_baku = fields.Boolean(
#         string="Is Jumlah Bahan Baku Visible", compute="_compute_visibility"
#     )
#     is_visible_hasil_produksi_cover = fields.Boolean(
#         string="Is Hasil Produksi Cover Visible", compute="_compute_visibility"
#     )
#     is_visible_qty_kirim_ke_uv = fields.Boolean(
#         string="Is Qty Kirim ke UV Visible", compute="_compute_visibility"
#     )
#     is_visible_qty_terima_dari_uv = fields.Boolean(
#         string="Is Qty Terima dari UV Visible", compute="_compute_visibility"
#     )
#     is_visible_hasil_produksi_isi = fields.Boolean(
#         string="Is Hasil Produksi Isi Visible", compute="_compute_visibility"
#     )
#     is_visible_hasil_join_cetak_isi = fields.Boolean(
#         string="Is Hasil Join Cetak Isi Visible", compute="_compute_visibility"
#     )
#     is_visible_hasil_pemotongan_akhir = fields.Boolean(
#         string="Is Hasil Pemotongan Akhir Visible", compute="_compute_visibility"
#     )
#     is_visible_qty_realita_buku = fields.Boolean(
#         string="Is Qty Realita Buku Visible", compute="_compute_visibility"
#     )
#
#     @api.depends('workcenter_id.name')
#     def _compute_visibility(self):
#         """
#         Compute field visibility based on workcenter_id.name.
#         """
#         for record in self:
#             # Default all fields to invisible
#             record.is_visible_jumlah_bahan_baku = False
#             record.is_visible_hasil_produksi_cover = False
#             record.is_visible_qty_kirim_ke_uv = False
#             record.is_visible_qty_terima_dari_uv = False
#             record.is_visible_hasil_produksi_isi = False
#             record.is_visible_hasil_join_cetak_isi = False
#             record.is_visible_hasil_pemotongan_akhir = False
#             record.is_visible_qty_realita_buku = False
#
#             # Set visibility based on the Workcenter Name
#             if record.workcenter_id.name == 'Produksi Cetak Cover':
#                 record.is_visible_jumlah_bahan_baku = True
#                 record.is_visible_hasil_produksi_cover = True
#             elif record.workcenter_id.name == 'Mengirimkan ke UV Varnish':
#                 record.is_visible_qty_kirim_ke_uv = True
#             elif record.workcenter_id.name == 'Menerima Cetak Cover dari UV Varnish':
#                 record.is_visible_qty_terima_dari_uv = True
#             elif record.workcenter_id.name == 'Produksi Cetak Isi':
#                 record.is_visible_jumlah_bahan_baku = True
#                 record.is_visible_hasil_produksi_isi = True
#             elif record.workcenter_id.name == 'Join Cetak Cover dan Isi':
#                 record.is_visible_hasil_join_cetak_isi = True
#             elif record.workcenter_id.name == 'Pemotongan Akhir':
#                 record.is_visible_hasil_pemotongan_akhir = True
#             elif record.workcenter_id.name == 'Packing Buku kedalam Box':
#                 record.is_visible_qty_realita_buku = True