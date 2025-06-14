from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError


class MrpBomCustom(models.Model):
    _inherit = 'mrp.bom'
    
    # Override the default product_tmpl_id field to add domain filter
    product_tmpl_id = fields.Many2one(
        'product.template', 
        string='Product',
        required=True,
        domain="[('tipe_kertas', 'in', ['a4', 'b5'])]",
        check_company=True,
        context={'default_tipe_kertas': 'a4', 'form_view_ref': 'product.product_template_form_view', 
                'no_create': True, 'no_create_edit': True, 'no_quick_create': True},
        # Use string representation for options to ensure it's properly passed
        options='{"no_create": true, "no_create_edit": true, "no_open": false}'
    )
    
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
    gramasi_kertas_isi = fields.Integer(string="Gramatur Kertas Isi (GSM)", default=70)
    gramasi_kertas_cover = fields.Integer(string="Gramatur Kertas Cover (GSM)", default=210)
    
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
    hrg_kertas_isi = fields.Integer(string="Harga Kertas Isi (Rp)", required=True)
    hrg_kertas_cover = fields.Integer(string="Harga Kertas Cover (Rp)", required=True)
    hrg_plate_isi = fields.Integer(string="Harga Plate Isi (Rp)", required=True)
    hrg_plate_cover = fields.Integer(string="Harga Plate Cover (Rp)", required=True)
    hrg_box = fields.Integer(string="Harga Box (Rp) /box", required=True)

    # === SECTION: Fields untuk biaya jasa ===
    jasa_cetak_isi = fields.Integer(string="Biaya Cetak Isi (Rp)", required=True)
    jasa_cetak_cover = fields.Integer(string="Biaya Cetak Cover (Rp)", required=True)
    jasa_jilid = fields.Float(string="Biaya Jilid (Rp) /hal", required=True)
    hrg_uv = fields.Float(string="Harga UV (Rp) /cm", required=True)

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
    @api.onchange('purchase_requisition_ids')
    def _onchange_purchase_requisition_ids(self):
        """
        Update harga material dan BoM lines saat Purchase Agreement ditambah/dihapus dari BOM.
        - Jika PA ditambah: Update harga dari PA dan tambahkan/update komponen dari PA.
        - Jika PA dihapus: Reset harga dan hapus komponen yang relevan.
        """
        self._compute_material_prices() # Panggil fungsi yang menghitung harga
        self._update_bom_lines_from_pa() # Panggil fungsi yang mengupdate bom_line_ids

    def _update_bom_lines_from_pa(self):
        """
        Membuat atau menghapus bom_line_ids berdasarkan produk di purchase_requisition_ids.
        Komponen yang ada di BoM lines tapi tidak ada di PA terpilih akan dihapus.
        Produk dari PA terpilih akan ditambahkan jika belum ada.
        """
        for bom in self:
            # Dapatkan semua product_id dari PA yang dipilih
            pa_product_ids = set()
            if bom.purchase_requisition_ids:
                for requisition in bom.purchase_requisition_ids:
                    for line in requisition.line_ids:
                        if line.product_id:
                            pa_product_ids.add(line.product_id.id)
            
            # Dapatkan product_id yang saat ini ada di bom_line_ids
            current_bom_product_ids = set(bom.bom_line_ids.mapped('product_id').ids)
            
            lines_to_add_vals = []
            lines_to_remove_ids = []

            # Identifikasi komponen yang akan ditambahkan
            for product_id_to_add in pa_product_ids:
                if product_id_to_add not in current_bom_product_ids:
                    # Cek domain product_id di MrpBomLineCustom ('tipe_kertas', 'not in', ['a4', 'b5'])
                    product = self.env['product.product'].browse(product_id_to_add)
                    if product.tipe_kertas not in ['a4', 'b5']:
                         lines_to_add_vals.append({
                            'product_id': product_id_to_add,
                            # product_qty akan dihitung oleh _onchange_product_id atau create/write di MrpBomLineCustom
                        })
            
            # Identifikasi komponen yang akan dihapus (yang ada di BoM tapi tidak lagi di PA terpilih)
            # Ini hanya akan menghapus komponen yang *sebelumnya* mungkin ditambahkan oleh PA.
            # Jika Anda ingin hanya menghapus komponen yang *persis* berasal dari PA yang baru saja di-deselect,
            # Anda memerlukan mekanisme tracking yang lebih kompleks.
            # Pendekatan ini menyinkronkan BoM lines dengan *semua* PA yang sedang dipilih.
            for bom_line in bom.bom_line_ids:
                if bom_line.product_id.id not in pa_product_ids:
                    # Hanya hapus jika produk tersebut valid sebagai komponen (bukan produk utama BoM)
                    if bom_line.product_id.tipe_kertas not in ['a4', 'b5']:
                        lines_to_remove_ids.append(bom_line.id)

            commands = []
            if lines_to_remove_ids:
                for line_id in lines_to_remove_ids:
                    commands.append(Command.delete(line_id)) # Atau Command.unlink(line_id)
            
            for vals in lines_to_add_vals:
                commands.append(Command.create(vals))
            
            if commands:
                bom.update({'bom_line_ids': commands})
                # Recompute operations might be needed if BoM type involves them
                # bom._onchange_bom_line_ids() # Jika ada onchange di bom_line_ids yang perlu dipicu


    # Menggunakan @api.depends agar _compute_material_prices juga dipanggil saat form load jika purchase_requisition_ids sudah terisi
    @api.depends('purchase_requisition_ids')
    def _compute_material_prices(self):
        """
        Mengambil harga material dari Purchase Agreement berdasarkan default_code product.
        Harga diambil dari Purchase Agreement yang terakhir ditambahkan ATAU yang memiliki harga lebih tinggi/rendah (sesuai kebutuhan).
        Saat ini mengambil dari yang terakhir teriterasi.
        """
        for bom in self:
            # Reset harga terlebih dahulu
            bom.hrg_kertas_isi = 0.0
            bom.hrg_kertas_cover = 0.0
            bom.hrg_plate_isi = 0.0
            bom.hrg_plate_cover = 0.0
            bom.hrg_box = 0.0

            if not bom.purchase_requisition_ids:
                return # Keluar jika tidak ada PA yang dipilih

            # Cek setiap Purchase Agreement yang dipilih
            # Jika ada beberapa PA dengan produk yang sama, logika ini akan mengambil harga dari PA terakhir dalam iterasi.
            # Anda mungkin perlu logika tambahan jika ingin memilih harga terendah/tertinggi/rata-rata.
            for requisition in bom.purchase_requisition_ids:
                for line in requisition.line_ids:
                    if not line.product_id or not line.product_id.default_code:
                        continue

                    default_code = line.product_id.default_code.lower()
                    
                    # Update harga berdasarkan default_code
                    if default_code == 'kertas_isi':
                        bom.hrg_kertas_isi = line.price_unit
                    elif default_code == 'kertas_cover':
                        bom.hrg_kertas_cover = line.price_unit
                    elif default_code == 'plate_isi':
                        bom.hrg_plate_isi = line.price_unit
                    elif default_code == 'plate_cover':
                        bom.hrg_plate_cover = line.price_unit
                    elif default_code == 'box':
                        bom.hrg_box = line.price_unit

    @api.constrains('hrg_kertas_isi', 'hrg_kertas_cover', 'hrg_plate_isi', 'hrg_plate_cover', 
                    'hrg_box', 'hrg_uv', 'jasa_cetak_isi', 'jasa_cetak_cover', 'jasa_jilid')
    def _check_required_prices(self):
        """
        Memvalidasi bahwa semua field harga dan biaya jasa telah diisi
        """
        # Cek ini hanya jika tidak ada PA yang dipilih, karena harga bisa datang dari PA
        # Atau, jika Anda ingin validasi ini selalu aktif, bahkan jika PA dipilih tapi tidak mengisi semua harga
        # Untuk sekarang, kita asumsikan jika PA dipilih, harga diharapkan dari sana.
        # Jika PA tidak mengisi semua harga, maka validasi ini bisa gagal.
        # Pertimbangkan apakah validasi ini masih relevan dengan cara kerja baru.
        # Mungkin lebih baik jika field harga ini tidak 'required=True' jika bisa diisi dari PA.
        for record in self:
            # Cek harga material
            if not record.hrg_kertas_isi == 0.0 and not record.hrg_kertas_isi : # contoh penyesuaian, izinkan 0 jika dari PA tidak ada
                 raise ValidationError('Harga Kertas Isi harus diisi atau di-set dari PA!')
            if not record.hrg_kertas_cover == 0.0 and not record.hrg_kertas_cover:
                 raise ValidationError('Harga Kertas Cover harus diisi atau di-set dari PA!')
            if not record.hrg_plate_isi:
                raise ValidationError('Harga Plate Isi harus diisi atau di-set dari PA!!')
            if not record.hrg_plate_cover:
                raise ValidationError('Harga Plate Cover harus diisi atau di-set dari PA!!')
            if not record.hrg_box:
                raise ValidationError('Harga Box harus diisi atau di-set dari PA!!')
            
            # Cek biaya jasa (ini biasanya manual, bukan dari PA material)
            if not record.jasa_cetak_isi:
                raise ValidationError('Biaya Cetak Isi harus diisi!')
            if not record.jasa_cetak_cover:
                raise ValidationError('Biaya Cetak Cover harus diisi!')
            if not record.jasa_jilid:
                raise ValidationError('Biaya Jilid harus diisi!')
            if not record.hrg_uv: 
                raise ValidationError('Harga UV harus diisi!')


    @api.constrains('bom_line_ids', 'purchase_requisition_ids')
    def _check_bom_lines(self):
        """
        Memvalidasi bahwa BOM memiliki tepat satu komponen untuk setiap tipe material yang diperlukan,
        baik dari BOM lines langsung atau dari Purchase Agreements.
        Tipe material yang diperlukan: isi, cover, plate_isi, plate_cover, dan box.
        """
        required_types = ['isi', 'cover', 'plate_isi', 'plate_cover', 'box']
        
        for bom in self:
            # Get all component types in this BOM
            component_types = {}
            
            # Check components from BOM lines
            for line in bom.bom_line_ids:
                if line.product_id:
                    tipe_kertas = line.product_id.product_tmpl_id.tipe_kertas
                    
                    # Check for duplicates of the same type
                    if tipe_kertas in component_types:
                        raise ValidationError(f'Duplikat komponen dengan tipe yang sama ditemukan: {dict(line.product_id.product_tmpl_id._fields["tipe_kertas"].selection).get(tipe_kertas)}. Silakan hapus salah satu.')
                    
                    # Add this component type to our tracking
                    component_types[tipe_kertas] = line.product_id.name
            
            # If Purchase Agreements are used, check for components there as well
            if bom.purchase_requisition_ids:
                for requisition in bom.purchase_requisition_ids:
                    for line in requisition.line_ids:
                        if line.product_id and line.product_id.product_tmpl_id.tipe_kertas:
                            tipe_kertas = line.product_id.product_tmpl_id.tipe_kertas
                            
                            # Don't check for duplicates across PA lines - allow same material type in different PAs
                            if tipe_kertas not in component_types:
                                component_types[tipe_kertas] = line.product_id.name
            
            # Check for missing required component types
            missing_types = []
            for req_type in required_types:
                if req_type not in component_types:
                    # Get the human-readable label for this type
                    type_label = dict(self.env['product.template']._fields['tipe_kertas'].selection).get(req_type)
                    missing_types.append(type_label)
            
            if missing_types:
                raise ValidationError(f'BOM harus memiliki tepat satu komponen untuk setiap tipe material berikut: {", ".join(missing_types)}. Material bisa berasal dari BOM Components atau Purchase Agreements.')
        
        
    @api.onchange('jenis_cetakan_isi', 'jenis_cetakan_cover', 'gramasi_kertas_isi', 'gramasi_kertas_cover', 
                'jmlh_halaman_buku', 'qty_buku', 'isi_box', 'waste_percentage', 'ukuran_kertas_cover',
                'ukuran_buku')
    def _onchange_bom_parameters(self):
        """
        When changing any BOM parameter that affects component quantities,
        automatically update the quantities of all components.
        """
        if self.bom_line_ids:
            waste_factor = 1 + (self.waste_percentage / 100)
            
            for line in self.bom_line_ids:
                if line.product_id:
                    product = line.product_id.product_tmpl_id
                    
                    # Update quantities based on component type
                    if product.tipe_kertas == 'isi':
                        # Calculate kertas isi quantity based on book parameters
                        line.product_qty = (self.kebutuhan_rim_isi * self.kebutuhan_kg_isi) * waste_factor
                    
                    elif product.tipe_kertas == 'cover':
                        # Calculate kertas cover quantity based on book parameters
                        line.product_qty = (self.kebutuhan_rim_cover * self.kebutuhan_kg_cover) * waste_factor
                    
                    elif product.tipe_kertas == 'plate_isi':
                        # Plate isi quantity based on print type
                        if self.jenis_cetakan_isi == '1_sisi':
                            line.product_qty = 4  # 4 plate CMYK
                        elif self.jenis_cetakan_isi == '2_sisi':
                            line.product_qty = 8  # 8 plate (2 sides)
                    
                    elif product.tipe_kertas == 'plate_cover':
                        # Plate cover quantity based on print type
                        if self.jenis_cetakan_cover == '1_sisi':
                            line.product_qty = 4
                        elif self.jenis_cetakan_cover == '2_sisi':
                            line.product_qty = 8
                    
                    elif line.product_id.default_code == 'BOX':
                        # Box quantity based on books per box and total quantity
                        line.product_qty = (self.qty_buku * waste_factor) / self.isi_box if self.isi_box > 0 else 0.0

    # Add this method to ensure values are saved when the record is written
    def write(self, vals):
        """Override write to ensure component quantities are updated when saving the record"""
        result = super(MrpBomCustom, self).write(vals)
        
        # If any of these fields were changed, update component quantities
        fields_to_check = ['jenis_cetakan_isi', 'jenis_cetakan_cover', 'gramasi_kertas_isi', 
                          'gramasi_kertas_cover', 'jmlh_halaman_buku', 'qty_buku', 
                          'isi_box', 'waste_percentage', 'ukuran_kertas_cover', 'ukuran_buku']
        
        if any(field in vals for field in fields_to_check):
            self._update_component_quantities()
            
        return result
    
    def _update_component_quantities(self):
        """Update component quantities based on current BOM parameters"""
        for bom in self:
            if not bom.bom_line_ids:
                continue
                
            waste_factor = 1 + (bom.waste_percentage / 100)
            
            for line in bom.bom_line_ids:
                if not line.product_id:
                    continue
                    
                product = line.product_id.product_tmpl_id
                new_qty = line.product_qty  # Default to current value
                
                # Calculate new quantity based on component type
                if product.tipe_kertas == 'isi':
                    new_qty = (bom.kebutuhan_rim_isi * bom.kebutuhan_kg_isi) * waste_factor
                elif product.tipe_kertas == 'cover':
                    new_qty = (bom.kebutuhan_rim_cover * bom.kebutuhan_kg_cover) * waste_factor
                elif product.tipe_kertas == 'plate_isi':
                    if bom.jenis_cetakan_isi == '1_sisi':
                        new_qty = 4
                    elif bom.jenis_cetakan_isi == '2_sisi':
                        new_qty = 8
                elif product.tipe_kertas == 'plate_cover':
                    if bom.jenis_cetakan_cover == '1_sisi':
                        new_qty = 4
                    elif bom.jenis_cetakan_cover == '2_sisi':
                        new_qty = 8
                elif line.product_id.default_code == 'BOX':
                    new_qty = (bom.qty_buku * waste_factor) / bom.isi_box if bom.isi_box > 0 else 0.0
                
                # Update the quantity if it changed
                if line.product_qty != new_qty:
                    line.sudo().write({'product_qty': new_qty})

class MrpBomLineCustom(models.Model):
    """
    Class ini buat handle detail komponen di BOM.
    Inherit dari mrp.bom.line bawaan Odoo.
    """
    _inherit = 'mrp.bom.line'
    
    # Override the product_id field with the domain filter
    product_id = fields.Many2one(
        'product.product',
        'Component',
        # Jika tipe_kertas ada di product.template:
        domain="[('product_tmpl_id.tipe_kertas', 'not in', ['a4', 'b5'])]",
        required=True
    )
    
    # Fields buat nyimpen hasil perhitungan kebutuhan material
    kebutuhan_rim_isi = fields.Float(string="Kebutuhan Rim Isi", compute="_compute_line_values", store=True)
    kebutuhan_kg_isi = fields.Float(string="Kebutuhan KG Isi", compute="_compute_line_values", store=True)
    kebutuhan_rim_cover = fields.Float(string="Kebutuhan Rim Cover", compute="_compute_line_values", store=True)
    kebutuhan_kg_cover = fields.Float(string="Kebutuhan KG Cover", compute="_compute_line_values", store=True)
    
    # Fields yang diambil dari BOM header
    isi_box = fields.Integer(related='bom_id.isi_box', string="Isi Box", store=True)
    qty_buku = fields.Integer(related='bom_id.qty_buku', string="Quantity Buku", store=True)

    # Function buat ngambil nilai kebutuhan dari BOM header
    @api.depends('bom_id', 'bom_id.kebutuhan_rim_isi', 'bom_id.kebutuhan_kg_isi', 
                 'bom_id.kebutuhan_rim_cover', 'bom_id.kebutuhan_kg_cover', 'bom_id.isi_box') # Menambahkan dependensi yang lebih spesifik
    def _compute_line_values(self):
        for line in self:
            bom = line.bom_id
            line.kebutuhan_rim_isi = bom.kebutuhan_rim_isi
            line.kebutuhan_kg_isi = bom.kebutuhan_kg_isi # KG per Rim dari BoM
            line.kebutuhan_rim_cover = bom.kebutuhan_rim_cover
            line.kebutuhan_kg_cover = bom.kebutuhan_kg_cover # KG per Rim dari BoM
            line.isi_box = bom.isi_box # Diambil dari related, tapi compute memastikan tersimpan jika store=True


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

    @api.constrains('product_id')
    def _check_product_id(self):
        """
        Memvalidasi bahwa product_id (component) telah diisi
        """
        for line in self:
            if not line.product_id:
                raise ValidationError('Komponen (Components) harus diisi! Silakan pilih material yang digunakan.')

    # @api.onchange('product_id')
    # def _onchange_product_id_warning(self):
    #     """
    #     Menampilkan warning jika product_id belum diisi
    #     """
    #     if not self.product_id:
    #         return {
    #             'warning': {
    #                 'title': 'Komponen Wajib Diisi',
    #                 'message': 'Silakan pilih material yang digunakan dalam BoM ini.'
    #             }
    #         }
