from odoo import models, fields, api


class MrpBomCustom(models.Model):
    _inherit = 'mrp.bom'

    # === SECTION: Fields untuk spesifikasi buku ===
    
    # Pilihan ukuran buku - B5 atau A4
    ukuran_buku = fields.Selection([
        ('b5', 'B5 (17.6 x 25 cm)'),
        ('a4', 'A4 (21 x 29.7 cm)')
    ], string="Ukuran Buku", default='b5')

    # Jenis cetakan untuk isi buku (1 sisi/2 sisi)
    # Default 2 sisi karena lebih hemat & umum dipake
    jenis_cetakan_isi = fields.Selection([
        ('1_sisi', 'Full Color 1 Sisi'),
        ('2_sisi', 'Full Color 2 Sisi')
    ], string="Jenis Cetakan Kertas Isi", default='2_sisi')

    # Jenis cetakan untuk cover (1 sisi/2 sisi)
    # Default 1 sisi karena biasanya cuma bagian luar yang dicetak
    jenis_cetakan_cover = fields.Selection([
        ('1_sisi', 'Full Color 1 Sisi'),
        ('2_sisi', 'Full Color 2 Sisi')
    ], string="Jenis Cetakan Kertas Cover", default='1_sisi')

    # === SECTION: Fields untuk biaya tambahan ===
    
    # Overhead: biaya operasional tambahan (listrik, sewa, dll)
    overhead_percentage = fields.Integer(
        string="Overhead (%)", 
        default=5,
        help="Persentase overhead yang dihitung dari total biaya"
    )
    
    # PPn: Pajak Pertambahan Nilai (11% sesuai aturan)
    ppn_percentage = fields.Integer(
        string="PPn (%)", 
        default=11,
        help="Persentase pajak PPn yang dihitung dari total biaya"
    )
    
    # Waste: Persentase tambahan untuk antisipasi kerusakan/gagal cetak
    waste_percentage = fields.Integer(
        string="Waste Produksi (%)", 
        default=10,
        help="Persentase tambahan untuk waste produksi"
    )

    # Fields hasil perhitungan overhead & ppn (dihitung otomatis)
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

    # === SECTION: Fields untuk spesifikasi teknis ===
    
    # Gramasi: berat kertas per meter persegi
    gramasi_kertas_isi = fields.Integer(string="Gramasi Kertas Isi (gram)", default=70)
    gramasi_kertas_cover = fields.Integer(string="Gramasi Kertas Cover (gram)", default=210)
    
    # Jumlah halaman & quantity
    jmlh_halaman_buku = fields.Integer(string="Jumlah Halaman Buku", default=160)
    qty_buku = fields.Integer(string="Quantity Buku", default=1)
    isi_box = fields.Integer(string="Isi Box (Jumlah Buku/Box)", default=60)
    
    # Jenis finishing
    jenis_jilid = fields.Selection([
        ('perfect_binding', 'Perfect Binding (Lem)'),
        ('stitching', 'Stitching (Kawat)')
    ], string="Jenis Jilid", default='perfect_binding')
    
    jenis_uv = fields.Selection([
        ('glossy', 'Glossy'),
        ('matte', 'Matte (Doff)')
    ], string="Jenis UV", default='glossy')

    # Field buat link ke Purchase Agreements
    purchase_requisition_ids = fields.Many2many(
        'purchase.requisition',
        string="Purchase Agreements",
        help="Pilih Purchase Agreements untuk BoM."
    )

    # === SECTION: Fields untuk harga material ===
    # Nanti bakal diisi otomatis dari Purchase Agreement, tapi untuk sementara manual input
    hrg_kertas_isi = fields.Integer(string="Harga Kertas Isi (Rp)")
    hrg_kertas_cover = fields.Integer(string="Harga Kertas Cover (Rp)")
    hrg_plate_isi = fields.Integer(string="Harga Plate Isi (Rp)")
    hrg_plate_cover = fields.Integer(string="Harga Plate Cover (Rp)")
    hrg_box = fields.Integer(string="Harga Box (Rp)")
    hrg_uv = fields.Float(string="Harga UV (Rp)")

    # Material price fields --> ini compute nya belum jalan hiks
    # hrg_kertas_isi = fields.Float(string="Harga Kertas Isi (Rp)", compute="_compute_material_prices", store=True)
    # hrg_kertas_cover = fields.Float(string="Harga Kertas Cover (Rp)", compute="_compute_material_prices", store=True)
    # hrg_plate_isi = fields.Float(string="Harga Plate Isi (Rp)", compute="_compute_material_prices", store=True)
    # hrg_plate_cover = fields.Float(string="Harga Plate Cover (Rp)", compute="_compute_material_prices", store=True)
    # hrg_box = fields.Float(string="Harga Box (Rp)", compute="_compute_material_prices", store=True)
    # hrg_uv = fields.Float(string="Harga UV (Rp)", compute="_compute_material_prices", store=True)

    # === SECTION: Fields untuk biaya jasa ===
    jasa_cetak_isi = fields.Integer(string="Biaya Cetak Isi (Rp)")
    jasa_cetak_cover = fields.Integer(string="Biaya Cetak Cover (Rp)")
    jasa_jilid = fields.Float(string="Biaya Jilid (Rp)")

    # === SECTION: Fields hasil perhitungan biaya bahan ===
    # Semua field ini dihitung otomatis (compute)
    total_biaya_kertas_isi = fields.Float(
        string="Total Biaya Kertas Isi", 
        compute="_compute_biaya_bahan_baku",
        store=True
    )
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

    # menambahkan field baru untuk melakukan kalkulasi quantity buku yang ditambah persentase waste
    qty_buku_plus_waste = fields.Float(
        string="Quantity Buku Plus Waste",
        compute="_compute_qty_buku_plus_waste",
        store=True,
        help="Jumlah buku yang disiapkan termasuk tambahan waste."
    )
    
    # Function buat ngitung quantity buku + waste
    @api.depends('qty_buku', 'waste_percentage')
    def _compute_qty_buku_plus_waste(self):
        """
        Ngehitung total buku yang harus disiapkan dengan tambahan waste.
        Misal: 
        - Qty buku = 1000
        - Waste 10%
        Total yang disiapkan = 1000 * (1 + 10/100) = 1100 buku
        """
        for bom in self:
            # Pastiin qty_buku ada dan waste percentage gak minus
            if bom.qty_buku and bom.waste_percentage >= 0:
                bom.qty_buku_plus_waste = bom.qty_buku * (1 + (bom.waste_percentage / 100))
            else:
                bom.qty_buku_plus_waste = bom.qty_buku

    # Function buat ngitung kebutuhan kertas (dalam rim dan kg)
    @api.depends('jmlh_halaman_buku', 'qty_buku', 'gramasi_kertas_isi', 'gramasi_kertas_cover', 'ukuran_buku')
    def _compute_hpp_values(self):
        """
        Ngehitung kebutuhan kertas dalam satuan rim dan kg.
        - Rim: 1 rim = 500 lembar
        - Kg: tergantung ukuran kertas dan gramasi
        
        Rumus kg = (panjang * lebar * gramasi) / 20000
        """
        for bom in self:
            # === Perhitungan Kertas Isi ===
            # Ngitung kebutuhan kg berdasarkan ukuran buku
            if bom.ukuran_buku == 'a4':
                # Ukuran plano A4: 63 x 86 cm
                kebutuhan_kg_isi = (63 * 86 * bom.gramasi_kertas_isi) / 20000
            elif bom.ukuran_buku == 'b5':
                # Ukuran plano B5: 54.6 x 73 cm
                kebutuhan_kg_isi = (54.6 * 73 * bom.gramasi_kertas_isi) / 20000
            else:
                kebutuhan_kg_isi = 0.0

            # Ngitung kebutuhan rim
            # Rumus: (jmlh halaman / 16 lembar per katern * qty buku) / 500 lembar per rim
            bom.kebutuhan_rim_isi = (bom.jmlh_halaman_buku / 16 * bom.qty_buku) / 500
            bom.kebutuhan_kg_isi = kebutuhan_kg_isi
            bom.kebutuhan_kertasIsi = bom.kebutuhan_rim_isi * kebutuhan_kg_isi

            # === Perhitungan Kertas Cover ===
            # Ngitung kebutuhan kg cover berdasarkan ukuran
            if bom.ukuran_buku == 'a4':
                # Ukuran plano cover A4: 65 x 100 cm
                kebutuhan_kg_cover = (65 * 100 * bom.gramasi_kertas_cover) / 20000
            elif bom.ukuran_buku == 'b5':
                # Ukuran plano cover B5: 79 x 55 cm
                kebutuhan_kg_cover = (79 * 55 * bom.gramasi_kertas_cover) / 20000
            else:
                kebutuhan_kg_cover = 0.0

            # Ngitung kebutuhan rim cover
            # Rumus: (qty buku / 4 cover per plano) / 500 lembar per rim
            bom.kebutuhan_rim_cover = (bom.qty_buku / 4) / 500
            bom.kebutuhan_kg_cover = kebutuhan_kg_cover
            bom.kebutuhan_kertasCover = bom.kebutuhan_rim_cover * kebutuhan_kg_cover

    # Function buat ngitung biaya bahan baku
    @api.depends('ukuran_buku', 'jenis_cetakan_isi', 'jenis_cetakan_cover', 'jmlh_halaman_buku', 
                'qty_buku', 'hrg_plate_isi', 'hrg_plate_cover', 'waste_percentage')
    def _compute_biaya_bahan_baku(self):
        for record in self:
            # Ngitung waste factor (misal: 10% = 0.1)
            waste_factor = (record.waste_percentage / 100)

            # === Ngitung biaya kertas isi ===
            kebutuhan_rim_isi = (record.jmlh_halaman_buku / 16 * record.qty_buku) / 500
            # Ngitung kg berdasarkan ukuran
            kebutuhan_kg_isi = (((63 * 86 * record.gramasi_kertas_isi) / 20000) if record.ukuran_buku == 'a4'
                                else ((54.6 * 73 * record.gramasi_kertas_isi) / 20000))
            # Total biaya = (kebutuhan * harga) + waste
            record.total_biaya_kertas_isi = (kebutuhan_rim_isi * kebutuhan_kg_isi * record.hrg_kertas_isi) + (
                    (kebutuhan_rim_isi * kebutuhan_kg_isi * record.hrg_kertas_isi) * waste_factor)

            # === Ngitung biaya kertas cover ===
            # (logika sama kayak kertas isi)
            kebutuhan_rim_cover = (record.qty_buku / 4) / 500
            kebutuhan_kg_cover = (((65 * 100 * record.gramasi_kertas_cover) / 20000) if record.ukuran_buku == 'a4'
                                  else (79 * 55 * record.gramasi_kertas_cover) / 20000)
            record.total_biaya_kertas_cover = (kebutuhan_rim_cover * kebutuhan_kg_cover * record.hrg_kertas_cover) + (
                    (kebutuhan_rim_cover * kebutuhan_kg_cover * record.hrg_kertas_cover) * waste_factor)

            # === Ngitung biaya plate isi ===
            # Jumlah plate tergantung jenis cetakan (1/2 sisi)
            if record.jenis_cetakan_isi == '1_sisi':
                plat_isi = 4  # 4 plate untuk 1 sisi
            elif record.jenis_cetakan_isi == '2_sisi':
                plat_isi = 8  # 8 plate untuk 2 sisi
            else:
                plat_isi = 0

            # Total biaya plate = jumlah katern * jumlah plate * harga plate
            record.total_biaya_plate_isi = (
                    (record.jmlh_halaman_buku / 16 * plat_isi) * record.hrg_plate_isi
            )

            # === Ngitung biaya plate cover ===
            # Jumlah plate cover tergantung jenis cetakan (1/2 sisi)
            if record.jenis_cetakan_cover == '1_sisi':  # Jika 1 sisi
                plat_cover = 4  # Butuh 4 plate (CMYK)
            elif record.jenis_cetakan_cover == '2_sisi':  # Jika 2 sisi
                plat_cover = 8  # Butuh 8 plate (CMYK x 2 sisi)
            else:
                plat_cover = 0  # Default jika tidak dipilih

            record.total_biaya_plate_cover = (plat_cover * record.hrg_plate_cover)

            # Ngitung biaya box
            # Rumus: jumlah box yang dibutuhin * harga per box
            record.total_biaya_box = (record.qty_buku / record.isi_box) * record.hrg_box

    # Function buat ngitung total biaya bahan baku
    @api.depends('total_biaya_kertas_isi', 'total_biaya_kertas_cover', 'total_biaya_plate_isi',
                 'total_biaya_plate_cover', 'total_biaya_box')
    def _compute_total_bahan_baku(self):
        for record in self:
            # Jumlah semua biaya bahan baku
            record.total_biaya_bahan_baku = (
                    record.total_biaya_kertas_isi
                    + record.total_biaya_kertas_cover
                    + record.total_biaya_plate_isi
                    + record.total_biaya_plate_cover
                    + record.total_biaya_box
            )

    # Function buat ngitung biaya jasa cetak dan finishing
    @api.depends('ukuran_buku', 'kebutuhan_rim_isi', 'kebutuhan_rim_cover', 'jasa_cetak_isi', 
                'jasa_cetak_cover', 'jasa_jilid', 'hrg_uv')
    def _compute_biaya_jasa(self):
        for record in self:
            # === Ngitung biaya cetak isi ===
            # Rumus: jumlah rim * biaya cetak per rim
            record.total_biaya_cetak_isi = record.kebutuhan_rim_isi * record.jasa_cetak_isi

            # === Ngitung biaya cetak cover ===
            # Rumus sama kayak cetak isi
            record.total_biaya_cetak_cover = record.kebutuhan_rim_cover * record.jasa_cetak_cover

            # === Ngitung biaya UV ===
            # Ukuran cover beda-beda tergantung ukuran buku
            if record.ukuran_buku == 'a4':
                ukuran_cover = 65 * 100  # cm2
            elif record.ukuran_buku == 'b5':
                ukuran_cover = 79 * 55  # cm2
            else:
                ukuran_cover = 0  

            # Ngitung waste berdasarkan input user
            waste_factor = 1 + (record.waste_percentage / 100)  # misal: 1.1 untuk waste 10%

            # Total biaya UV = (ukuran * harga UV per cm2) * jumlah rim * waste factor
            record.total_biaya_uv = (
                    (ukuran_cover * record.hrg_uv)  # Harga UV per cm2
                    * 500  # 1 rim
                    * (record.kebutuhan_rim_cover  # Jumlah rim
                       * waste_factor)  # Tambah waste
            )

            # === Ngitung biaya jilid ===
            # Rumus: jumlah halaman * biaya jilid per halaman * quantity
            record.total_biaya_jilid = record.jmlh_halaman_buku * record.jasa_jilid * record.qty_buku

    # Function buat ngitung total biaya jasa
    @api.depends('total_biaya_cetak_isi', 'total_biaya_cetak_cover', 'total_biaya_uv', 'total_biaya_jilid')
    def _compute_total_jasa(self):
        for record in self:
            # Jumlah semua biaya jasa
            record.total_biaya_jasa = (
                    record.total_biaya_cetak_isi
                    + record.total_biaya_cetak_cover
                    + record.total_biaya_uv
                    + record.total_biaya_jilid
            )

    # Function buat ngitung total akhir (termasuk overhead dan PPn)
    @api.depends('total_biaya_bahan_baku', 'total_biaya_jasa', 'qty_buku', 'overhead_percentage', 'ppn_percentage')
    def _compute_total_akhir(self):
        for record in self:
            # Total biaya dasar (bahan + jasa)
            total = record.total_biaya_bahan_baku + record.total_biaya_jasa
            
            # Hitung overhead (misal: 5% dari total biaya)
            record.overhead = total * (record.overhead_percentage / 100)
            
            # Hitung PPn (11% dari total + overhead)
            record.ppn = (total + record.overhead) * (record.ppn_percentage / 100)
            
            # Total HPP = total biaya + overhead + PPn
            record.hpp_total = total + record.overhead + record.ppn
            
            # HPP per buku = total HPP / jumlah buku
            record.hpp_per_unit = record.hpp_total / record.qty_buku

    '''Ini untuk menyamakan antara qty_buku yang ada dicustom dengan product_qty yang ada di BOM template'''

    # Function buat sinkronin qty_buku ke product_qty bawaan BOM
    @api.onchange('qty_buku')
    def _onchange_qty_buku(self):
        for record in self:
            record.product_qty = record.qty_buku

    # Function buat sinkronin product_qty bawaan BOM ke qty_buku
    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        for record in self:
            record.qty_buku = record.product_qty

    # Function buat ngambil harga material dari Purchase Agreement
    # Note: ini belum jalan, masih WIP
    @api.depends('purchase_requisition_ids')
    def _compute_material_prices(self):
        """Ngitung harga material berdasarkan Purchase Agreement yang dipilih."""
        for bom in self:
            # Reset semua harga dulu
            bom.hrg_kertas_isi = 0.0
            bom.hrg_kertas_cover = 0.0
            bom.hrg_plate_isi = 0.0
            bom.hrg_plate_cover = 0.0
            bom.hrg_box = 0.0
            bom.hrg_uv = 0.0

            # Bikin mapping nama produk ke field harga
            material_map = {
                'KERTAS_ISI': ['Kertas Isi (Virgin/HS)', 'Kertas Isi (Tabloid)'],
                'KERTAS_COVER': ['Kertas Cover (Art Carton)', 'Kertas Cover (Art Paper)',
                                'Kertas Cover (Ivory)', 'Kertas Cover (Boxboard)',
                                'Kertas Cover (Duplex)'],
                'PLATE_ISI': ['Plate Isi'],
                'PLATE_COVER': ['Plate Cover'],
                'BOX': ['Box Buku'],
                'UV': ['UV']
            }

            # Loop setiap Purchase Agreement yang dipilih
            for requisition in bom.purchase_requisition_ids:
                for line in requisition.line_ids:
                    product_name = line.product_id.name

                    # Cek tiap material dan update harganya
                    if any(name in product_name for name in material_map['KERTAS_ISI']):
                        bom.hrg_kertas_isi = line.price_unit
                        continue

                    # Check for Kertas Cover
                    if any(name in product_name for name in material_map['KERTAS_COVER']):
                        bom.hrg_kertas_cover = line.price_unit
                        continue

                    # Check for Plate Isi
                    if any(name in product_name for name in material_map['PLATE_ISI']):
                        bom.hrg_plate_isi = line.price_unit
                        continue

                    # Check for Plate Cover
                    if any(name in product_name for name in material_map['PLATE_COVER']):
                        bom.hrg_plate_cover = line.price_unit
                        continue

                    # Check for Box
                    if any(name in product_name for name in material_map['BOX']):
                        bom.hrg_box = line.price_unit
                        continue

                    # Check for UV
                    if any(name in product_name for name in material_map['UV']):
                        bom.hrg_uv = line.price_unit
                        continue


class MrpBomLineCustom(models.Model):
    _inherit = 'mrp.bom.line'

    # Fields tambahan di baris component
    kebutuhan_rim_isi = fields.Float(string="Kebutuhan Rim Isi", compute="_compute_line_values", store=True)
    kebutuhan_kg_isi = fields.Float(string="Kebutuhan KG Isi", compute="_compute_line_values", store=True)
    kebutuhan_rim_cover = fields.Float(string="Kebutuhan Rim Cover", compute="_compute_line_values", store=True)
    kebutuhan_kg_cover = fields.Float(string="Kebutuhan KG Cover", compute="_compute_line_values", store=True)
    isi_box = fields.Integer(related='bom_id.isi_box', string="Isi Box", store=True)
    qty_buku = fields.Integer(related='bom_id.qty_buku', string="Quantity Buku", store=True)

    # Function buat ngambil nilai kebutuhan dari BOM header
    @api.depends('bom_id')
    def _compute_line_values(self):
        """Ngambil nilai kebutuhan dari mrp.bom."""
        for line in self:
            bom = line.bom_id
            line.kebutuhan_rim_isi = bom.kebutuhan_rim_isi
            line.kebutuhan_kg_isi = bom.kebutuhan_kg_isi
            line.kebutuhan_rim_cover = bom.kebutuhan_rim_cover
            line.kebutuhan_kg_cover = bom.kebutuhan_kg_cover
            line.isi_box = bom.isi_box

    # Function buat update quantity komponen otomatis
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update otomatis quantity komponen berdasarkan tipe material (quantity (product_qty) berdasarkan product_id)."""
        for line in self:
            if line.product_id:
                bom = line.bom_id
                waste_factor = 1 + (bom.waste_percentage / 100)
                product = line.product_id.product_tmpl_id

                # Logika quantity untuk tiap tipe material
                if product.tipe_kertas == 'isi':
                    line.product_qty = (line.kebutuhan_rim_isi * line.kebutuhan_kg_isi) * waste_factor
                # Logika untuk Kertas Cover
                elif product.tipe_kertas == 'cover':
                    line.product_qty = (line.kebutuhan_rim_cover * line.kebutuhan_kg_cover) * waste_factor
                # Logika untuk Plate Isi
                elif product.tipe_kertas == 'plate_isi':
                    if bom.jenis_cetakan_isi == '1_sisi':
                        line.product_qty = 4  # 4 plate CMYK
                    elif bom.jenis_cetakan_isi == '2_sisi':
                        line.product_qty = 8  # 8 plate (2 sisi)
                # Logika untuk Plate Cover
                elif product.tipe_kertas == 'plate_cover':
                    if bom.jenis_cetakan_cover == '1_sisi':
                        line.product_qty = 4
                    elif bom.jenis_cetakan_cover == '2_sisi':
                        line.product_qty = 8
                # Logika untuk Box
                elif line.product_id.default_code == 'BOX':
                    line.product_qty = (line.qty_buku * waste_factor) / line.isi_box if line.isi_box > 0 else 0.0

    # Function yang dipanggil pas bikin BOM line baru
    @api.model
    def create(self, vals):
        """Hitung product_qty saat komponen baru dibuat"""
        vals = self._update_product_qty(vals)
        return super(MrpBomLineCustom, self).create(vals)

    # Function yang dipanggil pas update BOM line
    def write(self, vals):
        """Hitung ulang product_qty saat komponen BOM diperbarui"""
        vals = self._update_product_qty(vals)
        return super(MrpBomLineCustom, self).write(vals)

    # Helper function buat update quantity
    def _update_product_qty(self, vals):
        """Logic buat update product_qty sebelum simpan data"""
        product_id = vals.get('product_id') or self.product_id.id
        bom = self.bom_id or self.env['mrp.bom'].browse(vals.get('bom_id'))
        waste_factor = 1 + (bom.waste_percentage / 100)

        if product_id:
            product = self.env['product.product'].browse(product_id)
            product_tmpl = product.product_tmpl_id

            # Update quantity berdasarkan tipe material (product_qty : kertas isi, kertas cover, plate isi, plate cover, box)
            if product_tmpl.tipe_kertas == 'isi':
                vals['product_qty'] = (bom.kebutuhan_rim_isi * bom.kebutuhan_kg_isi) * waste_factor
            elif product_tmpl.tipe_kertas == 'cover':
                vals['product_qty'] = (bom.kebutuhan_rim_cover * bom.kebutuhan_kg_cover) * waste_factor
            elif product_tmpl.tipe_kertas == 'plate_isi':
                if bom.jenis_cetakan_isi == '1_sisi':
                    vals['product_qty'] = 4
                elif bom.jenis_cetakan_isi == '2_sisi':
                    vals['product_qty'] = 8
            elif product_tmpl.tipe_kertas == 'plate_cover':
                if bom.jenis_cetakan_cover == '1_sisi':
                    vals['product_qty'] = 4
                elif bom.jenis_cetakan_cover == '2_sisi':
                    vals['product_qty'] = 8
            elif product.default_code == 'BOX':
                vals['product_qty'] = (bom.qty_buku * waste_factor) / bom.isi_box if bom.isi_box > 0 else 0.0
        return vals
