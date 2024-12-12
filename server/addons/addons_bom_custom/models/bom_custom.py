from odoo import models, fields, api


class MrpBomCustom(models.Model):
    _inherit = 'mrp.bom'

    # Fields untuk ukuran buku
    ukuran_buku = fields.Selection([
        ('b5', 'B5 (17.6 x 25 cm)'),
        ('a4', 'A4 (21 x 29.7 cm)')
    ], string="Ukuran Buku", default='b5')

    # Fields  untuk jenis cetakan
    jenis_cetakan_isi = fields.Selection([
        ('1_sisi', 'Full Color 1 Sisi'),
        ('2_sisi', 'Full Color 2 Sisi')
    ], string="Jenis Cetakan Kertas Isi", default='2_sisi')

    jenis_cetakan_cover = fields.Selection([
        ('1_sisi', 'Full Color 1 Sisi'),
        ('2_sisi', 'Full Color 2 Sisi')
    ], string="Jenis Cetakan Kertas Cover", default='1_sisi')

    # Tambahkan field input untuk overhead, ppn, dan waste
    overhead_percentage = fields.Float(string="Overhead (%)",default=5.0,  help="Persentase overhead yang dihitung dari total biaya")
    ppn_percentage = fields.Float(string="PPn (%)", default=11.0, help="Persentase pajak PPn yang dihitung dari total biaya")
    waste_percentage = fields.Float(string="Waste Produksi (%)", default=10.0, help="Persentase tambahan untuk waste produksi")

    # Overwrite field lama (tidak perlu hardcode lagi)
    overhead = fields.Float(
        string="Overhead",
        compute="_compute_total_akhir",
        store=True,
        help="Hasil perhitungan overhead berdasarkan persentase input user"
    )
    ppn = fields.Float(
        string="PPn",
        compute="_compute_total_akhir",
        store=True,
        help="Hasil perhitungan pajak PPn berdasarkan persentase input user"
    )

    gramasi_kertas_isi = fields.Float(string="Gramasi Kertas Isi (gram)", default=70.0)
    gramasi_kertas_cover = fields.Float(string="Gramasi Kertas Cover (gram)", default=210.0)
    jmlh_halaman_buku = fields.Integer(string="Jumlah Halaman Buku", default=160)
    qty_buku = fields.Float(string="Quantity Buku", default=1.0)
    isi_box = fields.Float(string="Isi Box (Jumlah Buku/Box)", default=60.0)
    jenis_jilid = fields.Selection([
        ('perfect_binding', 'Perfect Binding (Lem)'),
        ('stitching', 'Stitching (Kawat)')
    ], string="Jenis Jilid", default='perfect_binding')
    jenis_uv = fields.Selection([
        ('glossy', 'Glossy'),
        ('matte', 'Matte (Doff)')
    ], string="Jenis UV", default='glossy')

    hrg_kertas_isi = fields.Float(string="Harga Kertas Isi (Rp)")
    hrg_kertas_cover = fields.Float(string="Harga Kertas Cover (Rp)")
    hrg_plate_isi = fields.Float(string="Harga Plate Isi (Rp)")
    hrg_plate_cover = fields.Float(string="Harga Plate Cover (Rp)")
    hrg_box = fields.Float(string="Harga Box (Rp)")
    hrg_uv = fields.Float(string="Harga UV (Rp)")

    jasa_cetak_isi = fields.Float(string="Biaya Cetak Isi (Rp)")
    jasa_cetak_cover = fields.Float(string="Biaya Cetak Cover (Rp)")
    jasa_jilid = fields.Float(string="Biaya Jilid (Rp)")

    total_biaya_kertas_isi = fields.Float(string="Total Biaya Kertas Isi", compute="_compute_biaya_bahan_baku",
                                          store=True)
    total_biaya_kertas_cover = fields.Float(string="Total Biaya Kertas Cover", compute="_compute_biaya_bahan_baku",
                                            store=True)
    total_biaya_plate_isi = fields.Float(string="Total Biaya Plate Isi", compute="_compute_biaya_bahan_baku",
                                         store=True)
    total_biaya_plate_cover = fields.Float(string="Total Biaya Plate Cover", compute="_compute_biaya_bahan_baku",
                                           store=True)
    total_biaya_box = fields.Float(string="Total Biaya Box", compute="_compute_biaya_bahan_baku", store=True)
    total_biaya_bahan_baku = fields.Float(string="Total Biaya Bahan Baku", compute="_compute_total_bahan_baku",
                                          store=True)

    total_biaya_cetak_isi = fields.Float(string="Total Biaya Cetak Isi", compute="_compute_biaya_jasa", store=True)
    total_biaya_cetak_cover = fields.Float(string="Total Biaya Cetak Cover", compute="_compute_biaya_jasa", store=True)
    total_biaya_uv = fields.Float(string="Total Biaya UV", compute="_compute_biaya_jasa", store=True)
    total_biaya_jilid = fields.Float(string="Total Biaya Jilid", compute="_compute_biaya_jasa", store=True)
    total_biaya_jasa = fields.Float(string="Total Biaya Jasa", compute="_compute_total_jasa", store=True)

    # overhead = fields.Float(string="Overhead (5%)", compute="_compute_total_akhir", store=True)
    # ppn = fields.Float(string="PPn (11%)", compute="_compute_total_akhir", store=True)
    hpp_total = fields.Float(string="HPP Total", compute="_compute_total_akhir", store=True)
    hpp_per_unit = fields.Float(string="HPP per Unit", compute="_compute_total_akhir", store=True)

    # Hasil Perhitungan dari HPP
    kebutuhan_rim_isi = fields.Float(string="Kebutuhan Kertas Isi (Rim)", compute="_compute_hpp_values", store=True)
    kebutuhan_kg_isi = fields.Float(string="Kebutuhan Kertas Isi (KG)", compute="_compute_hpp_values", store=True)
    kebutuhan_kertasIsi = fields.Float(string="Kebutuhan Kertas Isi", compute="_compute_hpp_values", store=True)

    kebutuhan_rim_cover = fields.Float(string="Kebutuhan Kertas Cover (Rim)", compute="_compute_hpp_values", store=True)
    kebutuhan_kg_cover = fields.Float(string="Kebutuhan Kertas Cover (KG)", compute="_compute_hpp_values", store=True)
    kebutuhan_kertasCover = fields.Float(string="Kebutuhan Kertas Cover", compute="_compute_hpp_values", store=True)

    isi_box = fields.Float(string="Isi Box", default=60.0)

    # menambahkan field baru untuk melakukan kalkulasi quantity buku yang ditambah persentase waste
    qty_buku_plus_waste = fields.Float(
        string="Quantity Buku Plus Waste",
        compute="_compute_qty_buku_plus_waste",
        store=True,
        help="Jumlah buku yang disiapkan termasuk tambahan waste."
    )

    @api.depends('qty_buku', 'waste_percentage')
    def _compute_qty_buku_plus_waste(self):
        """
        Menghitung jumlah buku yang harus disiapkan dengan waste percentage.
        """
        for bom in self:
            if bom.qty_buku and bom.waste_percentage >= 0:
                bom.qty_buku_plus_waste = bom.qty_buku * (1 + (bom.waste_percentage / 100))
            else:
                bom.qty_buku_plus_waste = bom.qty_buku  # Default ke qty_buku jika waste_percentage tidak valid

    @api.depends('jmlh_halaman_buku', 'qty_buku', 'gramasi_kertas_isi', 'gramasi_kertas_cover', 'ukuran_buku')
    def _compute_hpp_values(self):
        """Hitung kebutuhan rim dan kg berdasarkan formula HPP"""
        for bom in self:
            # Perhitungan Kertas Isi
            if bom.ukuran_buku == 'a4':
                # Logika perhitungan untuk ukuran A4
                kebutuhan_kg_isi = (63 * 86 * bom.gramasi_kertas_isi) / 20000
            elif bom.ukuran_buku == 'b5':
                # Logika perhitungan untuk ukuran B5
                kebutuhan_kg_isi = (54.6 * 73 * bom.gramasi_kertas_isi) / 20000
            else:
                kebutuhan_kg_isi = 0.0  # Default jika ukuran buku tidak dipilih

            bom.kebutuhan_rim_isi = (bom.jmlh_halaman_buku / 16 * bom.qty_buku) / 500
            bom.kebutuhan_kg_isi = kebutuhan_kg_isi
            bom.kebutuhan_kertasIsi = bom.kebutuhan_rim_isi * kebutuhan_kg_isi

            # Perhitungan Kertas Cover
            if bom.ukuran_buku == 'a4':
                # Logika perhitungan untuk ukuran A4
                kebutuhan_kg_cover = (65 * 100 * bom.gramasi_kertas_cover) / 20000
            elif bom.ukuran_buku == 'b5':
                # Logika perhitungan untuk ukuran B5
                kebutuhan_kg_cover = (79 * 55 * bom.gramasi_kertas_cover) / 20000
            else:
                kebutuhan_kg_cover = 0.0  # Default jika ukuran buku tidak dipilih

            bom.kebutuhan_rim_cover = (bom.qty_buku / 4) / 500
            bom.kebutuhan_kg_cover = kebutuhan_kg_cover
            bom.kebutuhan_kertasCover = bom.kebutuhan_rim_cover * kebutuhan_kg_cover

    # Perhitungan Biaya Bahan Baku
    @api.depends('jenis_cetakan_isi', 'jenis_cetakan_cover', 'jmlh_halaman_buku', 'qty_buku', 'hrg_plate_isi',
                 'hrg_plate_cover', 'waste_percentage')
    def _compute_biaya_bahan_baku(self):
        for record in self:
            # Perhitungan untuk cari HPP Produksi
            # Hitung Waste Factor
            waste_factor = (record.waste_percentage / 100)
            # Kertas Isi
            kebutuhan_rim_isi = (record.jmlh_halaman_buku / 16 * record.qty_buku) / 500
            kebutuhan_kg_isi = (((63 * 86 * record.gramasi_kertas_isi) / 20000) if record.ukuran_buku == 'a4'
                                   else ((54.6 * 73 * record.gramasi_kertas_isi) / 20000))
            record.total_biaya_kertas_isi = (kebutuhan_rim_isi * kebutuhan_kg_isi * record.hrg_kertas_isi) + ((kebutuhan_rim_isi * kebutuhan_kg_isi * record.hrg_kertas_isi) * waste_factor)

            # Kertas Cover
            kebutuhan_rim_cover = (record.qty_buku / 4) / 500
            kebutuhan_kg_cover = (((65 * 100 * record.gramasi_kertas_cover) / 20000) if record.ukuran_buku == 'a4'
                                     else (79 * 55 * record.gramasi_kertas_cover) / 20000)
            record.total_biaya_kertas_cover = (kebutuhan_rim_cover * kebutuhan_kg_cover * record.hrg_kertas_cover) + ((kebutuhan_rim_cover * kebutuhan_kg_cover * record.hrg_kertas_cover) * waste_factor)

            # Plate Isi
            if record.jenis_cetakan_isi == '1_sisi':  # Jika 1 sisi
                plat_isi = 4
            elif record.jenis_cetakan_isi == '2_sisi':  # Jika 2 sisi
                plat_isi = 8
            else:
                plat_isi = 0  # Default jika tidak dipilih

            record.total_biaya_plate_isi = (
                    (record.jmlh_halaman_buku / 16 * plat_isi) * record.hrg_plate_isi
            )

            # Kertas Cover (Plate Cover)
            if record.jenis_cetakan_cover == '1_sisi':  # Jika 1 sisi
                plat_cover = 4
            elif record.jenis_cetakan_cover == '2_sisi':  # Jika 2 sisi
                plat_cover = 8
            else:
                plat_cover = 0  # Default jika tidak dipilih

            record.total_biaya_plate_cover = (plat_cover * record.hrg_plate_cover)

            # Box
            record.total_biaya_box = (record.qty_buku / record.isi_box) * record.hrg_box

    # Total Biaya Bahan Baku
    @api.depends('total_biaya_kertas_isi', 'total_biaya_kertas_cover', 'total_biaya_plate_isi',
                 'total_biaya_plate_cover', 'total_biaya_box')
    def _compute_total_bahan_baku(self):
        for record in self:
            record.total_biaya_bahan_baku = (
                    record.total_biaya_kertas_isi
                    + record.total_biaya_kertas_cover
                    + record.total_biaya_plate_isi
                    + record.total_biaya_plate_cover
                    + record.total_biaya_box
            )

    # Perhitungan Biaya Jasa
    @api.depends('kebutuhan_rim_isi', 'kebutuhan_rim_cover','jasa_cetak_isi', 'jasa_cetak_cover', 'jasa_jilid', 'hrg_uv')
    def _compute_biaya_jasa(self):
        for record in self:
            # Cetak Isi
            # kebutuhan_isiRim = (record.jmlh_halaman_buku / 16 * record.qty_buku) / 500
            record.total_biaya_cetak_isi = record.kebutuhan_rim_isi * record.jasa_cetak_isi

            # Cetak Cover
            # kebutuhan_rim_cover = (record.qty_buku / 4) / 500
            record.total_biaya_cetak_cover = record.kebutuhan_rim_cover * record.jasa_cetak_cover

            # UV
            if record.ukuran_buku == 'a4':
                ukuran_cover = 65 * 100
            elif record.ukuran_buku == 'b5':
                ukuran_cover = 79 * 55
            else:
                ukuran_cover = 0  # Default jika ukuran_buku tidak dipilih

            # Waste berdasarkan input user
            waste_factor = 1 + (record.waste_percentage / 100)

            record.total_biaya_uv = (
                    (ukuran_cover * record.hrg_uv)  # Harga UV per cm
                    * 500  # 1 rim
                    * (record.kebutuhan_rim_cover  # Jumlah rim
                    + waste_factor)  # Tambah 10% Waste Produksi
            )

            # Jilid
            record.total_biaya_jilid = record.jmlh_halaman_buku * record.jasa_jilid * record.qty_buku

    # Total Biaya Jasa
    @api.depends('total_biaya_cetak_isi', 'total_biaya_cetak_cover', 'total_biaya_uv', 'total_biaya_jilid')
    def _compute_total_jasa(self):
        for record in self:
            record.total_biaya_jasa = (
                    record.total_biaya_cetak_isi
                    + record.total_biaya_cetak_cover
                    + record.total_biaya_uv
                    + record.total_biaya_jilid
            )

    # Perhitungan Overhead, PPn, dan HPP
    @api.depends('total_biaya_bahan_baku', 'total_biaya_jasa', 'qty_buku')
    def _compute_total_akhir(self):
        for record in self:
            total = record.total_biaya_bahan_baku + record.total_biaya_jasa
            # Hitung Overhead berdasarkan input user
            record.overhead = total * (record.overhead_percentage / 100)
            # Hitung PPn berdasarkan input user
            record.ppn = (total + record.overhead) * (record.ppn_percentage / 100)
            record.hpp_total = total + record.ppn
            record.hpp_per_unit = record.hpp_total / record.qty_buku #if record.qty_buku > 0 else 0.0

    '''Ini untuk menyamakan antara qty_buku yang ada dicustom dengan product_qty yang ada di BOM template'''
    # Sinkronisasi Qty Buku ke Quantity Bawaan BOM
    @api.onchange('qty_buku')
    def _onchange_qty_buku(self):
        for record in self:
            record.product_qty = record.qty_buku

    # Sinkronisasi Quantity Bawaan BOM ke Qty Buku
    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        for record in self:
            record.qty_buku = record.product_qty


# INI ANEH GABISA KL MASUKIN BYK PRODUCT -> QTY TDK KE SAVE.... TAPI SEBELUMNYA GAPAPA?!
# class MrpBomLineCustom(models.Model):
#     _inherit = 'mrp.bom.line'
#
#     # Field tambahan di baris component
#     kebutuhan_rim_isi = fields.Float(string="Kebutuhan Rim Isi", help="Hasil Perhitungan Rim Kertas Isi dari HPP", compute="_compute_line_values", store=True)
#     kebutuhan_kg_isi = fields.Float(string="Kebutuhan KG Isi", help="Hasil Perhitungan KG Kertas Isi dari HPP", compute="_compute_line_values", store=True)
#     kebutuhan_rim_cover = fields.Float(string="Kebutuhan Rim Cover", help="Hasil Perhitungan Rim Kertas Cover dari HPP", compute="_compute_line_values", store=True)
#     kebutuhan_kg_cover = fields.Float(string="Kebutuhan KG Cover", help="Hasil Perhitungan KG Kertas Cover dari HPP", compute="_compute_line_values", store=True)
#     isi_box = fields.Float(string="Isi Box", compute="_compute_line_values", store=True)
#     qty_buku = fields.Float(related='bom_id.qty_buku', string="Quantity Buku", store=True)
#
#     @api.depends('bom_id')
#     def _compute_line_values(self):
#         """Ambil nilai kebutuhan dari mrp.bom."""
#         for line in self:
#             bom = line.bom_id
#             line.kebutuhan_rim_isi = bom.kebutuhan_rim_isi
#             line.kebutuhan_kg_isi = bom.kebutuhan_kg_isi
#             line.kebutuhan_rim_cover = bom.kebutuhan_rim_cover
#             line.kebutuhan_kg_cover = bom.kebutuhan_kg_cover
#             line.isi_box = bom.isi_box
#
#     @api.onchange('product_id')
#     def _onchange_product_id(self):
#         """Update otomatis field quantity (product_qty) berdasarkan product_id."""
#         for line in self:
#             if line.product_id:
#                 product_name = line.product_id.name
#                 # Logika untuk Kertas Isi
#                 if "Kertas Isi" in product_name:
#                     line.product_qty = line.kebutuhan_rim_isi * line.kebutuhan_kg_isi
#                 # Logika untuk Kertas Cover
#                 elif "Kertas Cover" in product_name:
#                     line.product_qty = line.kebutuhan_rim_cover * line.kebutuhan_kg_cover
#                 # Logika untuk Box
#                 elif "Box" in product_name:
#                     line.product_qty = line.qty_buku / line.isi_box if line.isi_box > 0 else 0.0
#                 else:
#                     line.product_qty = 1.0  # Default jika tidak ada aturan
#
#     @api.model
#     def create(self, vals):
#         product = self.env['product.product'].browse(vals.get('product_id'))
#         if product:
#             if "Kertas Isi" in product.name:
#                 vals['product_qty'] = vals.get('kebutuhan_rim_isi', 0.0) * vals.get('kebutuhan_kg_isi', 0.0)
#             elif "Kertas Cover" in product.name:
#                 vals['product_qty'] = vals.get('kebutuhan_rim_cover', 0.0) * vals.get('kebutuhan_kg_cover', 0.0)
#             elif "Box" in product.name:
#                 vals['product_qty'] = vals.get('qty_buku', 0.0) / vals.get('isi_box', 1.0)
#         return super(MrpBomLineCustom, self).create(vals)

class MrpBomLineCustom(models.Model):
    _inherit = 'mrp.bom.line'

    # Field tambahan di baris component
    kebutuhan_rim_isi = fields.Float(string="Kebutuhan Rim Isi", compute="_compute_line_values", store=True)
    kebutuhan_kg_isi = fields.Float(string="Kebutuhan KG Isi", compute="_compute_line_values", store=True)
    kebutuhan_rim_cover = fields.Float(string="Kebutuhan Rim Cover", compute="_compute_line_values", store=True)
    kebutuhan_kg_cover = fields.Float(string="Kebutuhan KG Cover", compute="_compute_line_values", store=True)
    isi_box = fields.Float(string="Isi Box", compute="_compute_line_values", store=True)
    qty_buku = fields.Float(related='bom_id.qty_buku', string="Quantity Buku", store=True)

    @api.depends('bom_id')
    def _compute_line_values(self):
        """Ambil nilai kebutuhan dari mrp.bom."""
        for line in self:
            bom = line.bom_id
            line.kebutuhan_rim_isi = bom.kebutuhan_rim_isi
            line.kebutuhan_kg_isi = bom.kebutuhan_kg_isi
            line.kebutuhan_rim_cover = bom.kebutuhan_rim_cover
            line.kebutuhan_kg_cover = bom.kebutuhan_kg_cover
            line.isi_box = bom.isi_box

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update otomatis field quantity (product_qty) berdasarkan product_id."""
        for line in self:
            if line.product_id:
                bom = line.bom_id
                waste_factor = 1 + (bom.waste_percentage / 100)
                product_name = line.product_id.name

                # Logika untuk Kertas Isi
                if "Kertas Isi" in product_name:
                    line.product_qty = (line.kebutuhan_rim_isi * line.kebutuhan_kg_isi) * waste_factor
                # Logika untuk Kertas Cover
                elif "Kertas Cover" in product_name:
                    line.product_qty = (line.kebutuhan_rim_cover * line.kebutuhan_kg_cover) * waste_factor
                # Logika untuk Box
                elif "Box" in product_name:
                    line.product_qty = line.qty_buku / line.isi_box if line.isi_box > 0 else 0.0

    @api.model
    def create(self, vals):
        """Pastikan product_qty dihitung dengan benar saat record dibuat."""
        bom = self.env['mrp.bom'].browse(vals.get('bom_id'))
        product = self.env['product.product'].browse(vals.get('product_id'))
        if bom and product:
            waste_factor = 1 + (bom.waste_percentage / 100)
            if "Kertas Isi" in product.name:
                vals['product_qty'] = (vals.get('kebutuhan_rim_isi', 0.0) * vals.get('kebutuhan_kg_isi',
                                                                                     0.0)) * waste_factor
            elif "Kertas Cover" in product.name:
                vals['product_qty'] = (vals.get('kebutuhan_rim_cover', 0.0) * vals.get('kebutuhan_kg_cover',
                                                                                       0.0)) * waste_factor
            elif "Box" in product.name:
                vals['product_qty'] = vals.get('qty_buku', 0.0) / vals.get('isi_box', 1.0)
        return super(MrpBomLineCustom, self).create(vals)

    def write(self, vals):
        """Pastikan product_qty dihitung dengan benar saat record diperbarui."""
        for line in self:
            bom = line.bom_id
            product = line.product_id
            if bom and product:
                waste_factor = 1 + (bom.waste_percentage / 100)
                if "Kertas Isi" in product.name:
                    vals['product_qty'] = (line.kebutuhan_rim_isi * line.kebutuhan_kg_isi) * waste_factor
                elif "Kertas Cover" in product.name:
                    vals['product_qty'] = (line.kebutuhan_rim_cover * line.kebutuhan_kg_cover) * waste_factor
                elif "Box" in product.name:
                    vals['product_qty'] = line.qty_buku / line.isi_box if line.isi_box > 0 else 0.0
        return super(MrpBomLineCustom, self).write(vals)