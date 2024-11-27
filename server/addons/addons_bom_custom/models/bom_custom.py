from odoo import models, fields, api


class MrpBomCustom(models.Model):
    _inherit = 'mrp.bom'

    # Fields tambahan
    ukuran_buku = fields.Selection([
        ('b5', 'B5 (17.6 x 25 cm)'),
        ('a4', 'A4 (21 x 29.7 cm)')
    ], string="Ukuran Buku", default='b5')

    gramasi_kertas_isi = fields.Float(string="Gramasi Kertas Isi (gram)", default=70.0)
    gramasi_kertas_cover = fields.Float(string="Gramasi Kertas Cover (gram)", default=210.0)
    jmlh_halaman_buku = fields.Integer(string="Jumlah Halaman Buku", default=160)
    qty_buku = fields.Float(string="Quantity Buku", default=1.0)
    isi_box = fields.Float(string="Isi Box (Jumlah Buku/Box)", default=60.0)

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

    overhead = fields.Float(string="Overhead (5%)", compute="_compute_total_akhir", store=True)
    ppn = fields.Float(string="PPn (11%)", compute="_compute_total_akhir", store=True)
    hpp_total = fields.Float(string="HPP Total", compute="_compute_total_akhir", store=True)
    hpp_per_unit = fields.Float(string="HPP per Unit", compute="_compute_total_akhir", store=True)

    # Perhitungan Biaya Bahan Baku
    @api.depends('jmlh_halaman_buku', 'qty_buku', 'hrg_kertas_isi', 'hrg_kertas_cover', 'hrg_plate_isi',
                 'hrg_plate_cover', 'hrg_box')
    def _compute_biaya_bahan_baku(self):
        for record in self:
            # Kertas Isi
            kebutuhan_rim_isi = (record.jmlh_halaman_buku / 16 * record.qty_buku) / 500
            kebutuhan_kg_isi = (54.6 * 73 * record.gramasi_kertas_isi) / 20000
            record.total_biaya_kertas_isi = (
                                                        kebutuhan_rim_isi * kebutuhan_kg_isi * record.hrg_kertas_isi) * 1.1  # Tambah 10%

            # Kertas Cover
            kebutuhan_rim_cover = (record.qty_buku / 4) / 500
            kebutuhan_kg_cover = (79 * 55 * record.gramasi_kertas_cover) / 20000
            record.total_biaya_kertas_cover = (
                                                          kebutuhan_rim_cover * kebutuhan_kg_cover * record.hrg_kertas_cover) * 1.1  # Tambah 10%

            # Plate Isi
            record.total_biaya_plate_isi = (record.jmlh_halaman_buku / 16 * 8) * record.hrg_plate_isi

            # Plate Cover
            record.total_biaya_plate_cover = 4 * record.hrg_plate_cover

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
    @api.depends('jasa_cetak_isi', 'jasa_cetak_cover', 'jasa_jilid', 'hrg_uv')
    def _compute_biaya_jasa(self):
        for record in self:
            # Cetak Isi
            kebutuhan_rim_isi = (record.jmlh_halaman_buku / 16 * record.qty_buku) / 500
            record.total_biaya_cetak_isi = kebutuhan_rim_isi * record.jasa_cetak_isi

            # Cetak Cover
            kebutuhan_rim_cover = (record.qty_buku / 4) / 500
            record.total_biaya_cetak_cover = kebutuhan_rim_cover * record.jasa_cetak_cover

            # UV
            ukuran_cover = 79 * 55
            record.total_biaya_uv = (ukuran_cover * record.hrg_uv) * 500 * kebutuhan_rim_cover * 1.1  # Tambah 10%

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
            record.overhead = total * 0.05  # Overhead 5%
            record.ppn = total * 0.11  # PPn 11%
            record.hpp_total = total + record.overhead + record.ppn
            record.hpp_per_unit = record.hpp_total / record.qty_buku if record.qty_buku > 0 else 0.0


    # kebutuhan_rim_isi = fields.Float(string="Kebutuhan Rim Isi (BOM Header)", compute="_compute_kebutuhan", store=True)
    # kebutuhan_kg_isi = fields.Float(string="Kebutuhan KG Isi (BOM Header)", compute="_compute_kebutuhan", store=True)
    # kebutuhan_rim_cover = fields.Float(string="Kebutuhan Rim Cover (BOM Header)", compute="_compute_kebutuhan", store=True)
    # kebutuhan_kg_cover = fields.Float(string="Kebutuhan KG Cover (BOM Header)", compute="_compute_kebutuhan", store=True)
    # isi_box = fields.Float(string="Isi Box (Buku per Box)", compute="_compute_kebutuhan", store=True)
    #
    #
    # @api.depends('bom_line_ids')  # Melacak perubahan di komponen BOM
    # def _compute_kebutuhan(self):
    #     for bom in self:
    #         # Ambil semua komponen BOM
    #         kertas_isi = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == 'KERTAS_ISI')
    #         kertas_cover = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == 'KERTAS_COVER')
    #         box = bom.bom_line_ids.filtered(lambda l: l.product_id.default_code == 'BOX')
    #
    #         # Perhitungan untuk setiap field
    #         bom.kebutuhan_rim_isi = sum(line.kebutuhan_rim_isi for line in kertas_isi)
    #         bom.kebutuhan_kg_isi = sum(line.kebutuhan_kg_isi for line in kertas_isi)
    #         bom.kebutuhan_rim_cover = sum(line.kebutuhan_rim_cover for line in kertas_cover)
    #         bom.kebutuhan_kg_cover = sum(line.kebutuhan_kg_cover for line in kertas_cover)
    #         bom.isi_box = sum(line.isi_box for line in box)


# class MrpBomLineCustom(models.Model):
#     _inherit = 'mrp.bom.line'
#
#     # Tambahkan field pendukung jika diperlukan
#     kebutuhan_rim_isi = fields.Float(string="Kebutuhan Rim Isi", help="Jumlah rim untuk kertas isi.")
#     kebutuhan_kg_isi = fields.Float(string="Kebutuhan KG Isi", help="Berat kertas isi per rim (kg).")
#     kebutuhan_rim_cover = fields.Float(string="Kebutuhan Rim Cover", help="Jumlah rim untuk kertas cover.")
#     kebutuhan_kg_cover = fields.Float(string="Kebutuhan KG Cover", help="Berat kertas cover per rim (kg).")
#     qty_buku = fields.Float(related='bom_id.product_qty', string="Jumlah Buku", store=True)
#     isi_box = fields.Float(string="Isi Box", help="Jumlah buku per box.")
#
#     # Compute logic untuk product_qty
#     @api.depends('product_id', 'kebutuhan_rim_isi', 'kebutuhan_kg_isi', 'kebutuhan_rim_cover', 'kebutuhan_kg_cover',
#                  'qty_buku', 'isi_box')
#     def _compute_product_qty(self):
#         for line in self:
#             # Logika perhitungan berdasarkan product_id.default_code
#             if line.product_id.default_code == "Kertas Isi":
#                 line.product_qty = line.kebutuhan_rim_isi * line.kebutuhan_kg_isi
#             elif line.product_id.default_code == "Kertas Cover":
#                 line.product_qty = line.kebutuhan_rim_cover * line.kebutuhan_kg_cover
#             elif line.product_id.default_code == "Box":
#                 line.product_qty = line.qty_buku / line.isi_box if line.isi_box > 0 else 0
#             else:
#                 line.product_qty = 1.0  # Default untuk produk lain
#
#     # Override field product_qty agar dapat dihitung otomatis
#     product_qty = fields.Float(
#         string="Quantity",
#         compute="_compute_product_qty",
#         store=True,
#         readonly=False,  # Tetap bisa diedit manual jika diperlukan
#     )
