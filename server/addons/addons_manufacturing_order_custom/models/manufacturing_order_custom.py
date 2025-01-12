from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
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
        # compute="_compute_ukuran_bahan_kertas_isi",
        # store=True
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

    # ukuran_bahan_kertas_isi = fields.Char(
    #     string="Ukuran Bahan Kertas Isi",
    #     compute="_compute_ukuran_bahan_kertas_isi",
    #     store=True
    # )
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
    # @api.depends('sale_id.order_line.product_id')
    # def _compute_ukuran_bahan_kertas_isi(self):
    #     """
    #     Compute the Ukuran Bahan Kertas Isi based on the product in the linked sale order lines.
    #     """
    #     for production in self:
    #         # Ensure the sale order exists
    #         if production.sale_id and production.sale_id.order_line:
    #             # Get the first product in the sale order lines (assuming it's the primary product)
    #             product = production.sale_id.order_line[0].product_id
    #             if product:
    #                 if product.name == 'B5':
    #                     production.ukuran_bahan_kertas_isi = "54.6 x 73"
    #                 elif product.name == 'A4':
    #                     production.ukuran_bahan_kertas_isi = "63 x 86"
    #                 else:
    #                     production.ukuran_bahan_kertas_isi = "Tidak Diketahui"
    #             else:
    #                 production.ukuran_bahan_kertas_isi = "Tidak Diketahui"
    #         else:
    #             production.ukuran_bahan_kertas_isi = "Tidak Diketahui"

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
        return self.env.ref('addons_manufacturing_order_custom.action_report_surat_perjanjian_kerja').report_action(
            self)


# untuk mengedit custom quantity di bagian work order di Manufacturing Order
class MrpWorkorderCustom(models.Model):
    _inherit = "mrp.workorder"

    # Dropdown to select Work Center Step
    work_center_step = fields.Selection([
        ('produksi_cetak_cover', 'Produksi Cetak Cover'),
        ('mengirimkan_ke_uv_varnish', 'Mengirimkan ke UV Varnish'),
        ('menerima_dari_uv_varnish', 'Menerima Cetak Cover dari UV Varnish'),
        ('produksi_cetak_isi', 'Produksi Cetak Isi'),
        ('join_cetak_cover_dan_isi', 'Join Cetak Cover dan Isi'),
        ('pemotongan_akhir', 'Pemotongan Akhir'),
        ('packing_buku', 'Packing Buku kedalam Box'),
    ], string="Work Center Step", required=True)

    # Visibility Fields
    jumlah_bahan_baku_visible = fields.Boolean(compute="_compute_visibility", string="Jumlah Bahan Baku Visible")
    hasil_produksi_cover_visible = fields.Boolean(compute="_compute_visibility", string="Hasil Produksi Cover Visible")
    hasil_produksi_isi_visible = fields.Boolean(compute="_compute_visibility", string="Hasil Produksi Isi Visible")
    qty_kirim_ke_uv_visible = fields.Boolean(compute="_compute_visibility", string="Qty Kirim ke UV Visible")
    qty_terima_dari_uv_visible = fields.Boolean(compute="_compute_visibility", string="Qty Terima dari UV Visible")
    qty_realita_buku_visible = fields.Boolean(compute="_compute_visibility", string="Qty Realita Buku Visible")

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

    @api.depends("work_center_step")
    def _compute_visibility(self):
        """
        Compute the visibility of fields based on the selected Work Center step.
        """
        for record in self:
            step = record.work_center_step
            record.jumlah_bahan_baku_visible = step in ['produksi_cetak_cover', 'produksi_cetak_isi']
            record.hasil_produksi_cover_visible = step == 'produksi_cetak_cover'
            record.hasil_produksi_isi_visible = step == 'produksi_cetak_isi'
            record.qty_kirim_ke_uv_visible = step == 'mengirimkan_ke_uv_varnish'
            record.qty_terima_dari_uv_visible = step == 'menerima_dari_uv_varnish'
            record.qty_realita_buku_visible = step == 'packing_buku'

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

    # @api.constrains('jumlah_bahan_baku', 'custom_qty_to_produce', 'work_center_step')
    # def _check_jumlah_bahan_baku(self):
    #     for record in self:
    #         if record.work_center_step in ['produksi_cetak_cover', 'produksi_cetak_isi']:
    #             if record.jumlah_bahan_baku > record.custom_qty_to_produce:
    #                 raise ValidationError(_(
    #                     'Jumlah bahan baku tidak boleh melebihi maksimal bahan baku (%s)'
    #                     % record.custom_qty_to_produce
    #                 ))

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
        'production_id.bom_id.waste_percentage',
        'production_id.bom_id.kebutuhan_rim_isi',
        'production_id.bom_id.kebutuhan_kg_isi',
        'production_id.bom_id.kebutuhan_rim_cover',
        'production_id.bom_id.kebutuhan_kg_cover',
        'production_id.bom_id.isi_box',
        'operation_id.name'
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
        Compute custom_qty_to_produce dynamically based on work_center_step and BOM details.
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

                else:
                    workorder.custom_qty_to_produce = 0.0
            else:
                workorder.custom_qty_to_produce = 0.0

    @api.constrains('jumlah_bahan_baku', 'custom_qty_to_produce', 'work_center_step')
    def _check_jumlah_bahan_baku(self):
        """
        Ensure jumlah_bahan_baku does not exceed custom_qty_to_produce and
        is not less than 90% of custom_qty_to_produce for the selected Work Center Step.
        """
        for record in self:
            if record.work_center_step in ['produksi_cetak_cover', 'produksi_cetak_isi']:
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
        Warn if jumlah_bahan_baku exceeds custom_qty_to_produce or is less than 90% of it.
        """
        if self.work_center_step in ['produksi_cetak_cover', 'produksi_cetak_isi']:
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

    # untuk mengupdate qty_producing
    @api.depends('qty_production', 'qty_produced')
    def _update_qty_producing(self, quantity=False):
        if not quantity:
            quantity = self.qty_production - self.qty_produced
            if self.production_id.product_id.tracking == 'serial':
                quantity = 1.0 if float_compare(quantity, 0,
                                                precision_rounding=self.production_id.product_uom_id.rounding) > 0 else 0
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

    # Aggregated fields for Detail Produksi and Rekap Hasil Produksi
    hasil_produksi_cover_total = fields.Float(
        string="Total Hasil Produksi Cover",
        compute="_compute_aggregated_results",
        store=False
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
        Compute aggregated production results for all work orders in the same manufacturing order.
        """
        for workorder in self:
            workorders = workorder.production_id.workorder_ids
            workorder.hasil_produksi_cover_total = sum(workorders.mapped('hasil_produksi_cover'))
            workorder.qty_kirim_ke_uv_total = sum(workorders.mapped('qty_kirim_ke_uv'))
            workorder.qty_terima_dari_uv_total = sum(workorders.mapped('qty_terima_dari_uv'))
            workorder.hasil_produksi_isi_total = sum(workorders.mapped('hasil_produksi_isi'))
            workorder.hasil_join_cetak_isi_total = sum(workorders.mapped('hasil_join_cetak_isi'))
            workorder.hasil_pemotongan_akhir_total = sum(workorders.mapped('hasil_pemotongan_akhir'))
            workorder.qty_realita_buku_total = sum(workorders.mapped('qty_realita_buku'))


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
