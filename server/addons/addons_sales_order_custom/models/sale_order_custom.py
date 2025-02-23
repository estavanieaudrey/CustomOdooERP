# Import library yang dibutuhin
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from io import BytesIO
import base64

# Class utama buat custom Sales Order - nambahin fitur2 untuk perjanjian jual beli
class SaleOrderCustom(models.Model):
    """
    Class ini buat custom-in Sales Order.
    Nambahin fitur2 untuk perjanjian jual beli buku.
    """
    _inherit = 'sale.order'
    
    # Link ke Manufacturing Order
    # Biar gampang tracking: SO ini diproses di MO mana
    mo_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        help="Link to the related Manufacturing Order"
    )

    # === PASAL 2: Detail Produk ===
    # Field2 untuk nyimpen detail produk, kebanyakan diambil otomatis dari BoM
    
    # Detail isi buku (diambil dari BoM, field compute)
    # Misal: "HVS 70gsm (A4, Putih)"
    detail_isi = fields.Char(
        string="Detail Isi",
        compute="_compute_detail_isi",
        store=True  # Disimpen di database biar gak perlu ngitung ulang terus
    )
    
    # Detail cover buku (diambil dari BoM, field compute)
    # Misal: "Art Carton 230gsm (A3+, Glossy)"
    detail_cover = fields.Char(
        string="Detail Cover",
        compute="_compute_detail_cover",
        store=True
    )
    
    # Detail design (diisi manual sama user)
    detail_design = fields.Char(string="Design")
    
    # Dropdown untuk jenis jilid (diambil dari BoM)
    # Perfect binding = jilid lem
    # Stitching = jilid kawat
    jenis_jilid = fields.Selection([
        ('perfect_binding', 'Perfect Binding (Lem)'),  # Jilid pake lem
        ('stitching', 'Stitching (Kawat)')            # Jilid pake kawat
    ], string="Jenis Jilid", 
       compute="_compute_jenis_jilid", 
       store=True)

    # Dropdown untuk jenis UV (diambil dari BoM)
    # Glossy = mengkilap
    # Matte = doff/tidak mengkilap
    jenis_uv = fields.Selection([
        ('glossy', 'Glossy'),        # UV mengkilap
        ('matte', 'Matte (Doff)')    # UV doff/tidak mengkilap
    ], string="Jenis UV", 
       compute="_compute_jenis_uv", 
       store=True)

    # Detail packing (diambil dari BoM, dihitung otomatis)
    # Misal: "100 /box"
    detail_packing = fields.Char(
        string="Packing", 
        compute="_compute_detail_packing", 
        readonly=True
    )
    
    # Quantity buku (diambil dari BoM)
    detail_quantity = fields.Integer(
        related="bom_id.qty_buku", 
        string="Quantity Buku", 
        readonly=True
    )

    # === PASAL 3: Harga dan Pembayaran ===
    # Field2 untuk harga, diambil dari order line
    price_unit = fields.Float(
        related="order_line.price_unit", 
        string="Unit Price", 
        readonly=True
    )
    total_amount = fields.Monetary(
        related="amount_total", 
        string="Total Harga", 
        readonly=True
    )
    
    # Field2 untuk down payment
    down_payment_yes_no = fields.Boolean( # Toggle DP aktif/tidak
        string="Enable Down Payment",
        default=True,  # Default aktif
        help="Aktifkan atau nonaktifkan DP untuk pesanan ini."
    ) 
    # Default persentase DP 10% dan aktif
    down_payment_percentage = fields.Float(
        string="Down Payment Percentage", # Persentase DP
        default=10.0,  # Default 10%
        help="Persentase DP untuk pesanan ini."
    ) 
    down_payment_nominal = fields.Float(                                   
        string="Down Payment (Nominal)", 
        compute="_compute_down_payment_nominal", # Nominal DP (dihitung otomatis)
        store=True
    )
    
    # Field2 untuk data rekening transfer
    # Awalnya pake Many2one ke res.partner.bank & res.bank
    # Diganti jadi Char biar lebih simple
    # transfer_rekening_name = fields.Many2one('res.partner.bank', string="Nama Rekening")
    # transfer_rekening_bank = fields.Many2one('res.bank', string="Bank")
    transfer_rekening_name = fields.Char(string="Nama Rekening")
    transfer_rekening_bank = fields.Char(string="Bank")
    transfer_rekening_number = fields.Char(string="Nomor Rekening")
    transfer_rekening_branch = fields.Char(string="Cabang")

    # === PASAL 4: Expired Date dan Tanda Tangan ===
    expired_date = fields.Date(string="Expired Date")  # Tanggal kadaluarsa quotation
    # customer_signature = fields.Binary(string="Tanda Tangan", attachment=True)  # Deprecated, pake is_signed

    # Field untuk pilih BoM yang akan dipakai sebagai sumber data
    bom_id = fields.Many2one(
        'mrp.bom', 
        string="Bill of Materials", 
        help="Pilih BoM untuk mengambil data HPP."
    )
    
    # === Fields yang diambil dari BoM ===
    # Fields ini otomatis keisi waktu pilih BoM, readonly karena cuma bisa diubah dari BoM
    ukuran_buku = fields.Selection(
        related="bom_id.ukuran_buku", 
        string="Ukuran Buku", 
        readonly=True
    )
    jenis_cetakan_isi = fields.Selection(
        related="bom_id.jenis_cetakan_isi", 
        string="Jenis Cetakan Isi", 
        readonly=True
    )
    jenis_cetakan_cover = fields.Selection(
        related="bom_id.jenis_cetakan_cover", 
        string="Jenis Cetakan Cover", 
        readonly=True
    )
    jmlh_halaman_buku = fields.Integer(
        related="bom_id.jmlh_halaman_buku", 
        string="Jumlah Halaman Buku", 
        readonly=True
    )
    jasa_jilid = fields.Float(
        related="bom_id.jasa_jilid", 
        string="Biaya Jilid", 
        readonly=True
    )
    isi_box = fields.Integer(
        related="bom_id.isi_box", 
        string="Isi Box", 
        readonly=True
    )
    qty_buku = fields.Integer(
        related="bom_id.qty_buku", 
        readonly=True
    )
    hpp_per_unit = fields.Float(
        related="bom_id.hpp_per_unit", 
        string="Harga Satuan", 
        readonly=True
    )
    hpp_total = fields.Float(
        related="bom_id.hpp_total", 
        string="Harga Total", 
        readonly=True
    )
    ppn = fields.Float(
        related="bom_id.ppn", 
        string="PPn", 
        readonly=True
    )

    # Fields persentase dari BoM (semuanya integer)
    gramasi_kertas_isi = fields.Integer(related="bom_id.gramasi_kertas_isi", readonly=True)
    gramasi_kertas_cover = fields.Integer(related="bom_id.gramasi_kertas_cover", readonly=True)
    overhead_percentage = fields.Integer(related="bom_id.overhead_percentage", readonly=True)
    ppn_percentage = fields.Integer(related="bom_id.ppn_percentage", readonly=True)
    waste_percentage = fields.Integer(related="bom_id.waste_percentage", readonly=True)

    # === Functions untuk ngitung detail produk ===
    
    # Function buat ngitung detail isi dari BoM
    @api.depends('bom_id.bom_line_ids')
    def _compute_detail_isi(self):
        """
        Ngambil detail kertas isi dari komponen BoM.
        Misal: HVS 70gsm (A4, Putih)
        """
        for record in self:
            if record.bom_id:
                # Cari komponen yang namanya ada "Kertas Isi"
                isi_lines = record.bom_id.bom_line_ids.filtered(
                    lambda l: "Kertas Isi" in l.product_id.name
                )
                if isi_lines:
                    # Gabungin nama produk + variannya
                    detail_isi_list = [
                        f"{line.product_id.name} ({', '.join(line.product_id.product_template_variant_value_ids.mapped('name'))})"
                        for line in isi_lines
                    ]
                    record.detail_isi = ", ".join(detail_isi_list)
                else:
                    record.detail_isi = "Tidak Ada"
            else:
                record.detail_isi = "Tidak Ada"

    # Function buat ngitung detail cover, mirip kayak detail_isi
    @api.depends('bom_id.bom_line_ids')
    def _compute_detail_cover(self):
        """
        Ngambil detail kertas cover dari komponen BoM.
        Misal: Art Carton 230gsm (A3+, Glossy)
        """
        for record in self:
            if record.bom_id:
                # Cari komponen yang namanya ada "Kertas Cover"
                cover_lines = record.bom_id.bom_line_ids.filtered(
                    lambda l: "Kertas Cover" in l.product_id.name
                )
                if cover_lines:
                    # Gabungin nama produk + variannya
                    detail_cover_list = [
                        f"{line.product_id.name} ({', '.join(line.product_id.product_template_variant_value_ids.mapped('name'))})"
                        for line in cover_lines
                    ]
                    record.detail_cover = ", ".join(detail_cover_list)
                else:
                    record.detail_cover = "Tidak Ada"
            else:
                record.detail_cover = "Tidak Ada"

    # Dipanggil waktu BoM dipilih/ganti
    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """
        Auto-update order lines pas pilih BoM.
        Yang dikerjain:
        1. Reset order lines yang lama
        2. Ambil produk dari BoM
        3. Set quantity dan harga sesuai BoM
        """
        for record in self:
            if record.bom_id:
                # Hitung ulang field compute
                record._compute_detail_isi()
                record._compute_detail_cover()

                # Simpan hasil compute ke database
                record.write({
                    'detail_isi': record.detail_isi,
                    'detail_cover': record.detail_cover,
                })

    # Ngambil jenis jilid dari BoM
    @api.depends('bom_id.jenis_jilid')
    def _compute_jenis_jilid(self):
        """
        Ngambil jenis jilid dari BoM (perfect binding/stitching)
        """
        for record in self:
            if record.bom_id:
                # Ambil nilai jenis_jilid dari BoM
                record.jenis_jilid = record.bom_id.jenis_jilid
            else:
                # Default jika tidak ada BoM
                record.jenis_jilid = False

    # Ngambil jenis UV dari BoM
    @api.depends('bom_id.jenis_uv')
    def _compute_jenis_uv(self):
        """
        Ngambil jenis UV dari BoM (glossy/matte)
        """
        for record in self:
            if record.bom_id:
                # Ambil nilai jenis_uv dari BoM
                record.jenis_uv = record.bom_id.jenis_uv
            else:
                # Default jika tidak ada BoM
                record.jenis_uv = False

    # Ngitung detail packing di isi_box (tambahin "/box" di belakang angka)
    @api.depends('bom_id.isi_box')
    def _compute_detail_packing(self):
        """
        Bikin string detail packing.
        Misal: isi_box = 100 -> "100 /box"
        """
        for record in self:
            if record.bom_id.isi_box:
                record.detail_packing = f"{record.bom_id.isi_box} /box"
            else:
                record.detail_packing = "Tidak Ada"

    # Update data ke order lines waktu BoM dipilih
    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        if self.bom_id:
            # Reset order lines dulu biar bersih
            self.order_line = [(5, 0, 0)]

            # Tambah produk dari BoM ke order line
            product = self.bom_id.product_tmpl_id.product_variant_id
            if product:
                self.order_line = [(0, 0, {
                    'product_id': product.id,           # Produk dari BoM
                    'product_uom_qty': self.bom_id.qty_buku,  # Jumlah sesuai BoM
                    'price_unit': self.bom_id.hpp_per_unit,   # Harga per unit dari BoM
                    'name': product.name,               # Nama produk
                    'tax_id': [(6, 0, [])],            # Kosongkan pajak (udah include di hpp)
                })]
    
    # Field untuk draft perjanjian
    draft_perjanjian = fields.Binary(
        string="Draft Perjanjian PDF",  # File PDF-nya
        help="Upload draft perjanjian dalam format PDF"
    )
    draft_perjanjian_name = fields.Char(
        string="Nama File",          # Nama filenya
        help="Nama file draft perjanjian"
    )
    is_signed = fields.Boolean(
        string="Telah Ditandatangani", 
        default=False,  # Status ttd
        help="Centang jika perjanjian sudah ditandatangani"
    )
    signature_date = fields.Date(
        string="Tanggal Tanda Tangan",      # Tanggal ttd
        help="Tanggal perjanjian ditandatangani"
    )

    # Function buat bikin PDF dari template report yang udah dibuat
    def action_generate_pdf(self):
        """
        Function buat bikin PDF dari template report yang udah dibuat.
        Simpel sih, cuma manggil template reportnya terus dirender jadi PDF.
        """
        # Manggil template report yang udah didaftarin di XML, terus langsung dirender
        return self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian').report_action(self)

    # Override Method action_confirm di sale.order
    def action_confirm(self):
        """
        Override method confirm bawaan Odoo.
        Nambahin:
        1. Validasi draft perjanjian
        2. Auto-create MO
        """
        # Cek dulu ada draft perjanjiannya gak
        for order in self:
            if not order.draft_perjanjian:
                raise ValidationError("Upload Draft Perjanjian terlebih dahulu!")
                
        # Lanjutin pake logic confirm yang udah ada
        res = super(SaleOrderCustom, self).action_confirm()
        
        # Bikin draft Manufacturing Order
        for order in self:
            if order.bom_id:
                # Siapain data untuk bikin MO
                mo_vals = {
                    'product_id': order.bom_id.product_tmpl_id.product_variant_id.id,
                    'product_qty': order.qty_buku,
                    'bom_id': order.bom_id.id,
                    'sale_id': order.id,
                    'date_start': fields.Datetime.now(),
                    'origin': order.name,
                    'product_uom_id': order.bom_id.product_uom_id.id,
                    'state': 'draft',  # MO dibuat dalam status draft
                }
                self.env['mrp.production'].create(mo_vals)
        return res

    # Validasi: Pastiin ada draft perjanjian sebelum bisa ditandatangani
    @api.constrains('is_signed', 'draft_perjanjian')
    def _check_draft_perjanjian(self):
        """
        Validasi sebelum tanda tangan:
        - Harus ada draft perjanjian dulu
        - Kalo belum ada, lempar error
        """
        for record in self:
            if record.is_signed and not record.draft_perjanjian:
                raise ValidationError("Tidak dapat menandatangani perjanjian! Harap upload draft perjanjian terlebih dahulu.")

    # Update tanggal tanda tangan otomatis waktu status signed berubah
    @api.onchange('is_signed')
    def _onchange_is_signed(self):
        """
        Handle pas status signed berubah:
        - Kalo dicentang: Set tanggal hari ini
        - Kalo dimatiin: Reset tanggal
        - Validasi harus ada draft dulu
        """
        if self.is_signed:
            # Cek dulu ada draft perjanjiannya gak
            if not self.draft_perjanjian:
                self.is_signed = False
                return {
                    'warning': {
                        'title': 'Peringatan',
                        'message': 'Harap upload draft perjanjian terlebih dahulu sebelum menandatangani.'
                    }
                }
            # Set tanggal tanda tangan ke hari ini
            self.signature_date = fields.Date.today()
        else:
            # Reset tanggal kalo status signed dimatiin
            self.signature_date = False

    # Ngitung nominal DP dari persentase
    @api.depends('down_payment_percentage', 'hpp_total')
    def _compute_down_payment_nominal(self):
        """
        Hitung nominal Down Payment berdasarkan persentase.
        Rumus: total harga * persentase / 100
        """
        for record in self:
            # Cek dulu DP aktif gak & ada persentasenya gak
            if record.down_payment_yes_no and record.down_payment_percentage:
                # Rumus: total harga * persentase / 100
                record.down_payment_nominal = (record.hpp_total * record.down_payment_percentage) / 100
            else:
                record.down_payment_nominal = 0.0
                
    @api.onchange('down_payment_yes_no')
    def _onchange_down_payment_yes_no(self):
        """
        Handle pas checkbox DP di-toggle:
        - Kalo dicentang: hitung nominal DP
        - Kalo dimatiin: reset nilai DP jadi 0
        """
        for record in self:
            if record.down_payment_yes_no:
                # If percentage is already filled, calculate the nominal
                if record.down_payment_percentage:
                    record.down_payment_nominal = (record.hpp_total * record.down_payment_percentage) / 100
            else:
                # Reset values when down payment is disabled
                record.down_payment_percentage = 0.0
                record.down_payment_nominal = 0.0

    # Validasi persentase DP tidak boleh lebih dari 100%
    @api.constrains('down_payment_percentage')
    def _check_down_payment_percentage(self):
        for record in self:
            if record.down_payment_percentage > 100:
                raise ValidationError("Persentase down payment tidak bisa lebih dari 100%")

    @api.onchange('down_payment_percentage')
    def _onchange_down_payment_percentage(self):
        '''
        Memberikan peringatan secara real-time saat user menginput nilai dan 
        otomatis menyesuaikan nilai ke 100 jika melebihi batas
        '''
        if self.down_payment_percentage > 100:
            self.down_payment_percentage = 100
            return {
                'warning': {
                    'title': 'Peringatan',
                    'message': 'Persentase down payment tidak bisa lebih dari 100%'
                }
            }

    # Validasi: Pastiin ada BoM sebelum bisa disimpan
    @api.constrains('bom_id')
    def _check_bom_id(self):
        """
        Validasi sebelum simpan:
        - Harus ada BoM yang dipilih
        - Kalo belum ada, lempar error
        """
        for record in self:
            if not record.bom_id:
                raise ValidationError("Bill of Materials (BoM) harus dipilih terlebih dahulu!")

    # # Warning waktu save kalo belum pilih BoM
    # @api.onchange('bom_id')
    # def _onchange_bom_id_warning(self):
    #     """
    #     Kasih warning kalo BoM belum dipilih
    #     """
    #     if not self.bom_id:
    #         return {
    #             'warning': {
    #                 'title': 'BoM Wajib Dipilih',
    #                 'message': 'Silakan pilih Bill of Materials (BoM) terlebih dahulu sebelum menyimpan.'
    #             }
    #         }

    # # Override write method untuk validasi BoM
    # def write(self, vals):
    #     """
    #     Override write method untuk validasi BoM sebelum save
    #     """
    #     if not vals.get('bom_id') and not self.bom_id:
    #         raise ValidationError("Bill of Materials (BoM) harus dipilih terlebih dahulu!")
    #     return super(SaleOrderCustom, self).write(vals)

    # # Override create method untuk validasi BoM
    # @api.model
    # def create(self, vals):
    #     """
    #     Override create method untuk validasi BoM sebelum create
    #     """
    #     if not vals.get('bom_id'):
    #         raise ValidationError("Bill of Materials (BoM) harus dipilih terlebih dahulu!")
    #     return super(SaleOrderCustom, self).create(vals)

# Class khusus buat handle Down Payment
class SaleAdvancePaymentInv(models.TransientModel):
    """
    Class ini buat custom-in wizard Down Payment.
    Nambahin fitur:
    - Nominal DP yang dihitung otomatis
    - Pilihan fixed amount
    """
    _inherit = 'sale.advance.payment.inv'
    
    # Ganti hpp_total menjadi price_subtotal
    price_subtotal = fields.Float(
        string="Total Amount", 
        readonly=True,
        help="Total amount from sales order line"
    )
    nominal = fields.Float(
        string="Nominal", 
        readonly=True, 
        help="Computed Down Payment Nominal"
    )
    input_fixed_nominal = fields.Float(
        string="Fixed Amount", 
        help="Enter fixed amount for down payment"
    )
    max_nominal = fields.Float(
        string="Maximum Amount", 
        readonly=True, 
        help="Maximum allowed amount"
    )

    # Function buat ngatur pilihan metode pembayaran
    def _compute_advance_payment_method_selection(self):
        """
        Function ini buat ngatur pilihan metode pembayaran:
        - Regular invoice (bayar full)
        - Down payment pake persentase
        - Fixed amount (nominal tetap)
        """
        selection = [
            # ('all', 'Regular invoice'),      # Bayar full
            ('percentage', 'Percentage'),     # DP pake persentase
            ('fixed', 'Fixed amount')         # DP pake nominal tetap
        ]
        return selection

    # Field untuk pilihan metode pembayaran
    advance_payment_method = fields.Selection(
        selection=_compute_advance_payment_method_selection,
        string='Create Invoice',
        default='percentage',    # Default ke regular invoice
        required=True,    # Harus diisi
    )
    
    @api.onchange('amount', 'advance_payment_method')
    def _onchange_amount(self):
        """
        Update nominal saat amount (percentage) berubah
        """
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(sale_order_id)
            
            # Hitung total yang udah dibayar
            amount_invoiced = sum(sale_order.invoice_ids.mapped('amount_total'))
            # Hitung total yang harus dibayar (amount to invoice)
            amount_to_invoice = sale_order.hpp_total - amount_invoiced

            if self.advance_payment_method == 'percentage':
                # Hitung nominal berdasarkan persentase yang baru
                self.nominal = (amount_to_invoice * self.amount) / 100
                self.amount_to_invoice = amount_to_invoice

    # Function yang dipanggil waktu metode pembayaran berubah
    @api.onchange('advance_payment_method') 
    def _onchange_advance_payment_method(self):
        """
        Function untuk menghitung nominal berdasarkan metode pembayaran:
        - all: hpp_total - amount_invoiced (bayar full sisa)
        - percentage: (amount_to_invoice * amount / 100)
        - fixed: menggunakan fixed_amount yang diinput user
        """
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(sale_order_id)
            
            # Ambil price_subtotal dari sale order line
            self.price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
            
            # Hitung total yang udah dibayar
            amount_invoiced = sum(sale_order.invoice_ids.mapped('amount_total'))
            # Hitung total yang harus dibayar
            amount_to_invoice = self.price_subtotal - amount_invoiced
            
            if self.advance_payment_method == 'all':
                # Ambil total dari sale order line
                self.amount = amount_invoiced
                self.nominal = amount_to_invoice
                self.amount_to_invoice = amount_to_invoice
                
            
            elif self.advance_payment_method == 'percentage':
                # Down payment dengan persentase
                self.amount = sale_order.down_payment_percentage
                # Hitung nominal dari price_subtotal
                self.nominal = (self.price_subtotal * self.amount) / 100
                self.amount_to_invoice = amount_to_invoice
            
            elif self.advance_payment_method == 'fixed':
                # Fixed amount: pake nominal yang diinput user
                self.amount = 0.0  # Reset percentage amount
                self.max_nominal = amount_to_invoice
                self.amount_to_invoice = amount_to_invoice
                
                # Validasi nominal yang diinput gak boleh lebih dari max
                if self.input_fixed_nominal:
                    if self.input_fixed_nominal > self.max_nominal:
                        return {
                            'warning': {
                                'title': 'Warning',
                                'message': f'Maximum allowed amount is {self.max_nominal}'
                            }
                        }
                    self.nominal = self.input_fixed_nominal
            
            # Pastikan nominal gak minus
            self.nominal = max(0.0, self.nominal)
            
            # Update nilai nominal ke draft invoice (account.move.line)
            draft_invoice = self.env['account.move'].search([
                ('invoice_origin', '=', sale_order.name),
                ('state', '=', 'draft')
            ], limit=1)
            
            if draft_invoice:
                for line in draft_invoice.invoice_line_ids:
                    line.price_subtotal = self.nominal  # Update price_subtotal di invoice line

    @api.onchange('amount') #Menghitung ulang nominal DP saat jumlah persentase berubah untuk memastikan nilai DP selalu sesuai dengan total harga produksi.

    def _onchange_amount(self):
        """
        Update nominal saat amount (percentage) berubah
        """
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id and self.advance_payment_method == 'percentage':
            sale_order = self.env['sale.order'].browse(sale_order_id)
            price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
            
            # Hitung nominal berdasarkan persentase dari price_subtotal
            self.nominal = (price_subtotal * self.amount) / 100
            

    @api.model #Menetapkan nilai awal untuk wizard pembuatan invoice DP dengan mengambil data dari Sales Order, termasuk subtotal harga dan jumlah yang telah difakturkan.
    def default_get(self, fields):
        """
        Set nilai default saat wizard pertama kali dibuka
        """
        res = super(SaleAdvancePaymentInv, self).default_get(fields)
        
        if self._context.get('active_id'):
            sale_order = self.env['sale.order'].browse(self._context.get('active_id'))
            
            # Ambil price_subtotal dari sale order line
            price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
            
            # Hitung total yang udah dibayar
            amount_invoiced = sum(sale_order.invoice_ids.mapped('amount_total'))
            # Hitung total yang harus dibayar
            amount_to_invoice = price_subtotal - amount_invoiced
            
            # Set nilai default
            res.update({
                'price_subtotal': price_subtotal,
                'amount_invoiced': amount_invoiced,
                'amount_to_invoice': amount_to_invoice,
                'nominal': amount_to_invoice if res.get('advance_payment_method') == 'all' else 0.0
            })
            
        return res

    # Function buat kirim quotation + PDF ke email
    def action_quotation_send(self):
        """
        Function buat override cara kirim quotation bawaan Odoo.
        Bedanya ini nambah attachment PDF custom kita ke emailnya.
        """
        # Panggil dulu function aslinya dari Odoo
        action = super(SaleOrderCustom, self).action_quotation_send()
        
        # Cek ada context-nya gak (buat mastiin gak error)
        if action.get('context'):
            # Bikin PDF-nya
            pdf_content = self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian')._render_qweb_pdf(self.id)[0]
            
            # Convert PDF ke base64 biar bisa disimpen di database
            pdf_base64 = base64.b64encode(pdf_content)

            # Bikin nama file yang keren
            attachment_name = f"Quotation - {self.name or 'Draft'}.pdf"

            # Masukin attachment ke context email
            # Format (0, 0, values) itu command Odoo buat create record baru
            action['context']['default_attachment_ids'] = [(0, 0, {
                'name': attachment_name,  # Nama filenya mandatory)
                'datas': pdf_base64,      # Isi PDF-nya dalam base64
                'res_model': 'sale.order', # Model yang punya file ini
                'res_id': self.id,         # ID record yang punya
                'mimetype': 'application/pdf', # Tipe file
            })]
        return action