from odoo import models, fields, api


class MrpBomCustom(models.Model):
    _inherit = 'mrp.bom'

    # === SECTION: Fields untuk spesifikasi buku ===
    
    # Pilihan ukuran buku - B5 atau A4
    # Default B5 karena lebih umum dipake
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

    # Tambahkan field untuk pilihan ukuran kertas cover
    ukuran_kertas_cover = fields.Selection([
        ('65x100', '65 x 100'),
        ('79x109', '79 x 109')
    ], string="Ukuran Kertas Cover", default='65x100',
       help="Pilihan ukuran kertas cover untuk buku A4. B5 akan otomatis menggunakan 79 x 55")

    # === SECTION: Fields untuk biaya tambahan ===
    
    # Overhead: biaya operasional kayak listrik, sewa, dll
    # Default 5% dari total biaya
    overhead_percentage = fields.Integer(
        string="Overhead (%)", 
        default=5,
        help="Persentase overhead yang dihitung dari total biaya"
    )
    
    # PPn: Pajak yang wajib dibayar ke pemerintah
    # Default 11% sesuai aturan pajak Indonesia
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
    @api.onchange('ukuran_buku')
    def _onchange_ukuran_buku(self):
        """
        Filter dan set product_tmpl_id berdasarkan ukuran_buku yang dipilih.
        Juga mengatur ukuran_kertas_cover berdasarkan ukuran_buku:
        - Untuk B5: selalu 79x55, field disembunyikan
        - Untuk A4: tampilkan pilihan 65x100 atau 79x109
        
        Cara kerja:
        1. Filter products yang tipe_kertas nya sesuai ukuran_buku
        2. Set domain untuk product_tmpl_id
        3. Reset product_tmpl_id kalo ukurannya gak cocok
        4. Set ukuran_kertas_cover sesuai ukuran_buku
        """
        result = {'domain': {'product_tmpl_id': []}}
        
        if self.ukuran_buku:
            # Cari product yang sesuai dengan ukuran yang dipilih
            ProductTemplate = self.env['product.template']
            if self.ukuran_buku == 'a4':
                matching_products = ProductTemplate.search([('tipe_kertas', '=', 'a4')])
                # Set product pertama yang ditemukan (jika ada)
                if matching_products:
                    self.product_tmpl_id = matching_products[0].id
                else:
                    self.product_tmpl_id = False
                # Set domain untuk membatasi pilihan product
                result['domain']['product_tmpl_id'] = [('tipe_kertas', '=', 'a4')]
                
                # Untuk A4, set default ke 65x100 jika belum dipilih
                if not self.ukuran_kertas_cover:
                    self.ukuran_kertas_cover = '65x100'
            
            elif self.ukuran_buku == 'b5':
                matching_products = ProductTemplate.search([('tipe_kertas', '=', 'b5')])
                # Set product pertama yang ditemukan (jika ada)
                if matching_products:
                    self.product_tmpl_id = matching_products[0].id
                else:
                    self.product_tmpl_id = False
                # Set domain untuk membatasi pilihan product
                result['domain']['product_tmpl_id'] = [('tipe_kertas', '=', 'b5')]
                
                # Untuk B5, tidak perlu pilihan ukuran kertas cover
                self.ukuran_kertas_cover = False
        
        else:
            # Jika tidak ada ukuran yang dipilih, reset product dan ukuran_kertas_cover
            self.product_tmpl_id = False
            self.ukuran_kertas_cover = False
            
        return result

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """
        Set ukuran_buku otomatis berdasarkan tipe_kertas dari product yang dipilih
        """
        if self.product_tmpl_id:
            if self.product_tmpl_id.tipe_kertas == 'a4':
                self.ukuran_buku = 'a4'
            elif self.product_tmpl_id.tipe_kertas == 'b5':
                self.ukuran_buku = 'b5'
    
    # Function buat ngitung quantity buku + waste
    @api.depends('qty_buku', 'waste_percentage')
    def _compute_qty_buku_plus_waste(self):
        """
        Ngehitung total buku yang harus disiapkan termasuk waste.
        
        Contoh:
        - Kalo pesan 1000 buku
        - Waste 10%
        - Yang disiapkan = 1000 + (1000 * 10%) = 1100 buku
        
        Ini penting buat antisipasi buku yang rusak pas produksi
        """
        for bom in self:
            # Pastiin qty_buku ada dan waste percentage gak minus
            if bom.qty_buku and bom.waste_percentage >= 0:
                bom.qty_buku_plus_waste = bom.qty_buku * (1 + (bom.waste_percentage / 100))
            else:
                bom.qty_buku_plus_waste = bom.qty_buku

    # Function buat ngitung kebutuhan kertas (dalam rim dan kg)
    @api.depends('jmlh_halaman_buku', 'qty_buku', 'gramasi_kertas_isi', 'gramasi_kertas_cover', 'ukuran_buku', 'ukuran_kertas_cover')
    def _compute_hpp_values(self):
        """
        Ngehitung kebutuhan kertas dalam satuan rim dan kg.
        
        Info penting:
        - 1 rim = 500 lembar kertas
        - Rumus kg = (panjang * lebar * gramasi) / 20000
        - Ukuran kertas beda-beda tergantung A4 atau B5
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
                if bom.ukuran_kertas_cover == '65x100':
                    kebutuhan_kg_cover = (65 * 100 * bom.gramasi_kertas_cover) / 20000
                else:  # '79x109'
                    kebutuhan_kg_cover = (79 * 109 * bom.gramasi_kertas_cover) / 20000
            elif bom.ukuran_buku == 'b5':
                # B5 selalu menggunakan ukuran 79 x 55
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
                'qty_buku', 'hrg_plate_isi', 'hrg_plate_cover', 'waste_percentage', 'ukuran_kertas_cover')
    def _compute_biaya_bahan_baku(self):
        """
        Ngitung total biaya bahan yang dipake.
        
        Yang dihitung:
        - Kertas isi + waste
        - Kertas cover + waste (dengan ukuran yang bisa dipilih untuk A4)
        - Plate cetak isi (tergantung 1/2 sisi)
        - Plate cetak cover (tergantung 1/2 sisi)
        - Box packaging
        """
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

            # === Biaya kertas cover ===
            # Logikanya sama kayak kertas isi
            kebutuhan_rim_cover = (record.qty_buku / 4) / 500
            
            # Update perhitungan kebutuhan_kg_cover berdasarkan ukuran yang dipilih
            if record.ukuran_buku == 'a4':
                if record.ukuran_kertas_cover == '65x100':
                    kebutuhan_kg_cover = (65 * 100 * record.gramasi_kertas_cover) / 20000
                else:  # '79x109'
                    kebutuhan_kg_cover = (79 * 109 * record.gramasi_kertas_cover) / 20000
            else:  # B5
                kebutuhan_kg_cover = (79 * 55 * record.gramasi_kertas_cover) / 20000

            record.total_biaya_kertas_cover = (kebutuhan_rim_cover * kebutuhan_kg_cover * record.hrg_kertas_cover) + (
                    (kebutuhan_rim_cover * kebutuhan_kg_cover * record.hrg_kertas_cover) * waste_factor)

            # === Biaya plate isi ===
            # Jumlah plate tergantung 1 sisi atau 2 sisi
            if record.jenis_cetakan_isi == '1_sisi':
                plat_isi = 4  # CMYK = 4 warna = 4 plate
            elif record.jenis_cetakan_isi == '2_sisi':
                plat_isi = 8  # CMYK 2 sisi = 8 plate
            else:
                plat_isi = 0

            # Total = jumlah katern * jumlah plate * harga per plate
            record.total_biaya_plate_isi = (
                    (record.jmlh_halaman_buku / 16 * plat_isi) * record.hrg_plate_isi
            )

            # === Biaya plate cover ===
            # Sama kayak plate isi, tergantung 1/2 sisi
            if record.jenis_cetakan_cover == '1_sisi':
                plat_cover = 4  # CMYK 1 sisi
            elif record.jenis_cetakan_cover == '2_sisi':
                plat_cover = 8  # CMYK 2 sisi
            else:
                plat_cover = 0

            record.total_biaya_plate_cover = (plat_cover * record.hrg_plate_cover)

            # === Biaya box ===
            # Rumus: jumlah box yang dibutuhin * harga per box
            # Jumlah box = qty buku / kapasitas per box
            record.total_biaya_box = (record.qty_buku / record.isi_box) * record.hrg_box

    # Function buat ngitung total biaya bahan baku
    @api.depends('total_biaya_kertas_isi', 'total_biaya_kertas_cover', 'total_biaya_plate_isi',
                 'total_biaya_plate_cover', 'total_biaya_box')
    def _compute_total_bahan_baku(self):
        """
        Ngejumlahin semua biaya bahan baku.
        Simple aja: total = kertas isi + kertas cover + plate isi + plate cover + box
        """
        for record in self:
            record.total_biaya_bahan_baku = (
                    record.total_biaya_kertas_isi
                    + record.total_biaya_kertas_cover
                    + record.total_biaya_plate_isi
                    + record.total_biaya_plate_cover
                    + record.total_biaya_box
            )

    # Function buat ngitung biaya jasa cetak dan finishing
    @api.depends('ukuran_buku', 'kebutuhan_rim_isi', 'kebutuhan_rim_cover', 'jasa_cetak_isi', 
                'jasa_cetak_cover', 'jasa_jilid', 'hrg_uv', 'ukuran_kertas_cover')
    def _compute_biaya_jasa(self):
        """
        Ngitung semua biaya jasa yang dipake buat produksi.
        
        Yang dihitung:
        - Jasa cetak isi (per rim)
        - Jasa cetak cover (per rim)
        - UV coating buat cover
        - Jasa jilid (binding)
        """
        for record in self:
            # === Biaya cetak isi ===
            # Simple: jumlah rim * biaya per rim
            record.total_biaya_cetak_isi = record.kebutuhan_rim_isi * record.jasa_cetak_isi

            # === Biaya cetak cover ===
            # Sama kayak cetak isi
            record.total_biaya_cetak_cover = record.kebutuhan_rim_cover * record.jasa_cetak_cover

            # === Biaya UV ===
            # UV coating buat cover buku, ukurannya beda-beda
            if record.ukuran_buku == 'a4':
                if record.ukuran_kertas_cover == '65x100':
                    ukuran_cover = 65 * 100  # cm2 untuk A4 dengan ukuran 65x100
                else:  # '79x109'
                    ukuran_cover = 79 * 109  # cm2 untuk A4 dengan ukuran 79x109
            elif record.ukuran_buku == 'b5':
                ukuran_cover = 79 * 55   # cm2 untuk B5
            else:
                ukuran_cover = 0  

            # Tambah waste factor buat jaga-jaga
            waste_factor = 1 + (record.waste_percentage / 100)

            # Total UV = (ukuran * harga per cm2) * jumlah rim * waste
            record.total_biaya_uv = (
                    (ukuran_cover * record.hrg_uv)  # Harga per area
                    * 500  # Konversi ke rim
                    * (record.kebutuhan_rim_cover * waste_factor)  # Total kebutuhan + waste
            )

            # === Biaya jilid ===
            # Total = jumlah halaman * biaya per halaman * jumlah buku
            record.total_biaya_jilid = record.jmlh_halaman_buku * record.jasa_jilid * record.qty_buku

    # Function buat ngitung total biaya jasa
    @api.depends('total_biaya_cetak_isi', 'total_biaya_cetak_cover', 'total_biaya_uv', 'total_biaya_jilid')
    def _compute_total_jasa(self):
        """
        Ngejumlahin semua biaya jasa.
        Total = cetak isi + cetak cover + UV + jilid
        """
        for record in self:
            record.total_biaya_jasa = (
                    record.total_biaya_cetak_isi
                    + record.total_biaya_cetak_cover
                    + record.total_biaya_uv
                    + record.total_biaya_jilid
            )

    # Function buat ngitung total akhir (termasuk overhead dan PPn)
    @api.depends('total_biaya_bahan_baku', 'total_biaya_jasa', 'qty_buku', 'overhead_percentage', 'ppn_percentage')
    def _compute_total_akhir(self):
        """
        Ngitung total biaya akhir termasuk overhead dan pajak.
        
        Urutan hitungnya:
        1. Total biaya dasar = bahan + jasa
        2. Tambah overhead (misal 5%)
        3. Tambah PPn (11%)
        4. Bagi total dengan jumlah buku buat dapet harga per unit
        """
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
        """
        Fungsi ini mastiin qty_buku kita selalu sama dengan product_qty di BOM template.
        Jadi kalo kita ubah qty_buku, product_qty ikut berubah.
        """
        for record in self:
            record.product_qty = record.qty_buku

    # Function buat sinkronin product_qty bawaan BOM ke qty_buku
    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """
        Kebalikannya dari fungsi di atas.
        Kalo product_qty diubah, qty_buku juga ikut berubah.
        """
        for record in self:
            record.qty_buku = record.product_qty

    # Function buat ngambil harga material dari Purchase Agreement
    # Note: ini belum jalan, masih WIP
    @api.depends('purchase_requisition_ids')
    def _compute_material_prices(self):
        """
        Ngambil harga material dari Purchase Agreement yang dipilih.
        
        Cara kerjanya:
        1. Reset semua harga dulu
        2. Cek setiap Purchase Agreement yang dipilih
        3. Cocokin nama produk dengan kategorinya
        4. Update harga sesuai kategori
        
        Note: Ini masih WIP (Work in Progress), belum jalan sempurna
        """
        for bom in self:
            # Reset semua harga ke 0
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

            # Cek setiap Purchase Agreement
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
    """
    Class ini buat handle detail komponen di BOM.
    Inherit dari mrp.bom.line bawaan Odoo.
    """
    _inherit = 'mrp.bom.line'

    # Fields buat nyimpen hasil perhitungan kebutuhan material
    kebutuhan_rim_isi = fields.Float(string="Kebutuhan Rim Isi", compute="_compute_line_values", store=True)
    kebutuhan_kg_isi = fields.Float(string="Kebutuhan KG Isi", compute="_compute_line_values", store=True)
    kebutuhan_rim_cover = fields.Float(string="Kebutuhan Rim Cover", compute="_compute_line_values", store=True)
    kebutuhan_kg_cover = fields.Float(string="Kebutuhan KG Cover", compute="_compute_line_values", store=True)
    
    # Fields yang diambil dari BOM header
    isi_box = fields.Integer(related='bom_id.isi_box', string="Isi Box", store=True)
    qty_buku = fields.Integer(related='bom_id.qty_buku', string="Quantity Buku", store=True)

    # Function buat ngambil nilai kebutuhan dari BOM header
    @api.depends('bom_id')
    def _compute_line_values(self):
        """
        Ngambil nilai-nilai kebutuhan material dari BOM header.
        Ini dipake buat ngitung quantity komponen secara otomatis.
        """
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
