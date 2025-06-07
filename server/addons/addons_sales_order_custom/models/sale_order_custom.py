# Import library yang dibutuhin
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _
from io import BytesIO
import base64
from datetime import date
import logging
_logger = logging.getLogger(__name__)
import os


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
    
    # Detail design (diubah dari Char menjadi Binary untuk upload file design)
    nama_design = fields.Char(string="Design")
    
    detail_design = fields.Binary(
        string="File Design",
        help="Upload file design dalam format JPG, PNG, atau PDF"
    )
    detail_design_name = fields.Char(
        string="Nama File Design",
        help="Nama file design"
    )

    @api.constrains('detail_design', 'detail_design_name')
    def _check_design_file_format(self):
        """
        Validasi untuk memastikan file design yang diupload adalah format yang valid.
        """
        valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        
        for record in self:
            if record.detail_design and record.detail_design_name:
                # Extract file extension properly
                filename = record.detail_design_name.lower()
                file_ext = os.path.splitext(filename)[1]
                
                if file_ext not in valid_extensions:
                    raise ValidationError(f"File design harus dalam format JPG, PNG, atau PDF. Format yang diunggah: {file_ext}")    

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
        string="Down Payment Percentage (%)", # Persentase DP
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

    # === PASAL 4: Expired Date ===
    expired_date = fields.Date(
        string="Expired Date",
        related="validity_date",
        store=True,
        readonly=False,
        help="Tanggal kadaluarsa quotation (diambil dari Validity Date bawaan Odoo)"
    )
    # customer_signature = fields.Binary(string="Tanda Tangan", attachment=True)  # Deprecated, pake is_signed

    # Field untuk pilih BoM yang akan dipakai sebagai sumber data
    bom_id = fields.Many2one(
        'mrp.bom', 
        string="References of Bill of Materials", 
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
    
    def action_generate_all_invoice(self):
        """
        Function buat bikin PDF dari template report yang udah dibuat.
        Simpel sih, cuma manggil template reportnya terus dirender jadi PDF.
        """
        # Manggil template report yang udah didaftarin di XML, terus langsung dirender
        return self.env.ref('addons_sales_order_custom.action_all_invoices').report_action(self)

    # Override Method action_confirm di sale.order
    def action_confirm(self):
        """
        Override method confirm bawaan Odoo.
        Nambahin:
        1. Validasi draft perjanjian
        2. Auto-create MO
        """
        # Simpan signature_date sebelum confirm untuk masing-masing order
        signature_dates = {order.id: order.signature_date for order in self}

        # Cek dulu ada draft perjanjiannya gak
        for order in self:
            if not order.draft_perjanjian:
                raise ValidationError("Upload Draft Perjanjian terlebih dahulu!")
            
            # Tambahkan validasi is_signed harus True
            if not order.is_signed:
                raise ValidationError("Perjanjian harus ditandatangani terlebih dahulu! Silakan centang 'Telah Ditandatangani'.")
                
        # Lanjutin pake logic confirm yang udah ada
        res = super(SaleOrderCustom, self).action_confirm()
        
        # Kembalikan signature_date yang hilang
        for order in self:
            if order.id in signature_dates and signature_dates[order.id]:
                # Update signature_date langsung ke database untuk memastikan perubahan tersimpan
                self.env.cr.execute("""
                    UPDATE sale_order 
                    SET signature_date = %s
                    WHERE id = %s
                """, (
                    signature_dates[order.id],
                    order.id
                ))
                # Refresh value dari database
                order.invalidate_recordset(['signature_date'])
    
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
    
    # Validasi format file PDF
    @api.constrains('draft_perjanjian', 'draft_perjanjian_name')
    def _check_draft_perjanjian_format(self):
        """
        Validasi untuk memastikan file yang diupload adalah PDF.
        """
        for record in self:
            if record.draft_perjanjian and record.draft_perjanjian_name:
                if not record.draft_perjanjian_name.endswith('.pdf'):
                    raise ValidationError("File yang diupload harus dalam format PDF.")

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
            # Cek dulu ada draft perjanjian gak
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

    @api.onchange('expired_date')
    def _onchange_expired_date(self):
        """
        Validasi expired_date yang sudah tersync dengan validity_date
        """
        if self.expired_date == date.today():
            return {
                'warning': {
                    'title': "Warning",
                    'message': f"Apakah anda yakin jatuh tempo sales order adalah {date.today()}?",
                }
            }
            
    # Field untuk menampilkan total remaining amount dari semua order lines
    remaining_amount = fields.Monetary(
        string="Remaining Amount",
        compute="_compute_remaining_amount",
        store=True,
        help="Total remaining amount to be paid after considering all invoices."
    )
    
    @api.depends('amount_total', 'invoice_ids', 'invoice_ids.state', 'invoice_ids.amount_total', 'invoice_ids.payment_state')
    def _compute_remaining_amount(self):
        for order in self:
            # Calculate the total amount from confirmed invoices
            paid_amount = sum(
                invoice.amount_total 
                for invoice in order.invoice_ids 
                if invoice.state == 'posted' and invoice.payment_state in ['paid', 'partial']
            )
            
            # Remaining amount is the total order amount minus what's been paid
            order.remaining_amount = order.amount_total - paid_amount
            
    # Add total remaining quantity field
    total_remaining_qty = fields.Float(
        string="Total Remaining Qty",
        compute="_compute_total_remaining_qty",
        store=True,
        help="Total quantity that still needs to be delivered across all order lines"
    )
    
    @api.depends('order_line.remaining_qty')
    def _compute_total_remaining_qty(self):
        for order in self:
            order.total_remaining_qty = sum(line.remaining_qty for line in order.order_line)
            
    # Add a computed field to determine if the order is fully paid
    is_fully_paid = fields.Boolean(
        string="Is Fully Paid",
        compute="_compute_is_fully_paid",
        store=True,
        help="Technical field to check if the order is fully paid"
    )
    
    @api.depends('amount_total', 'invoice_ids', 'invoice_ids.state', 'invoice_ids.amount_total', 'invoice_ids.payment_state')
    def _compute_is_fully_paid(self):
        """
        Compute whether the sale order has been fully paid
        """
        for order in self:
            # Calculate posted invoice amounts
            posted_invoice_total = sum(
                invoice.amount_total 
                for invoice in order.invoice_ids 
                if invoice.state == 'posted'
            )
            
            # Calculate total sale order amount
            price_subtotal = sum(order.order_line.mapped('price_subtotal'))
            
            # Check if the total invoiced amount equals or exceeds the order subtotal
            # Adding a small margin (0.01) to account for rounding differences
            order.is_fully_paid = (posted_invoice_total >= (price_subtotal - 0.01))
    
    # Override the action_view_invoice method to disable the "Create Invoice" button
    def action_view_invoice(self, invoices=None):
        """
        Override the standard method to check if the order is fully paid
        before showing the invoice creation option
        
        @param invoices: Optional parameter for the invoices to display
        """
        # Get the standard action dictionary
        action = super(SaleOrderCustom, self).action_view_invoice(invoices=invoices)
        
        # Check if the order is fully paid
        if self.is_fully_paid:
            # Modify the context to exclude the 'create' option
            if action.get('context'):
                ctx = action.get('context')
                if isinstance(ctx, str):
                    # If context is a string (it might be in some cases)
                    ctx_dict = eval(ctx)
                    ctx_dict['show_create_button'] = False
                    action['context'] = str(ctx_dict)
                else:
                    # If context is already a dict
                    action['context'].update({'show_create_button': False})
            
            # Optional: Add a warning message
            action['help'] = "This order has been fully invoiced. No more invoices can be created."
            
        return action
    
    amount_undiscounted = fields.Monetary(
        string='Amount Before Discount',
        compute='_compute_amount_undiscounted',
        store=True,
    )
    
    total_discount_value = fields.Monetary(
        string='Total Discount Value',
        compute='_compute_discount_totals',
        store=True,
    )
    
    total_discount_percentage = fields.Float(
        string='Total Discount Percentage',
        compute='_compute_discount_totals',
        store=True,
        digits=(5, 2),
    )
    
    @api.depends('order_line.price_unit', 'order_line.product_uom_qty')
    def _compute_amount_undiscounted(self):
        for order in self:
            total = 0.0
            for line in order.order_line:
                total += line.price_unit * line.product_uom_qty
            order.amount_undiscounted = total
    
    @api.depends('order_line.discount', 'order_line.price_unit', 'order_line.product_uom_qty')
    def _compute_discount_totals(self):
        for order in self:
            total_discount = 0.0
            total_before_discount = 0.0
            
            for line in order.order_line:
                price = line.price_unit
                qty = line.product_uom_qty
                discount = line.discount / 100.0
                
                line_total_before = price * qty
                line_discount_amount = line_total_before * discount
                
                total_discount += line_discount_amount
                total_before_discount += line_total_before
            
            order.total_discount_value = total_discount
            order.total_discount_percentage = 0.0 if total_before_discount == 0 else (total_discount / total_before_discount) * 100
    
    @api.depends('order_line.price_unit', 'order_line.product_uom_qty')
    def _compute_amount_undiscounted(self):
        for order in self:
            total = 0.0
            for line in order.order_line:
                total += line.price_unit * line.product_uom_qty
            order.amount_undiscounted = total
            
    def action_cancel(self):
        """
        Override action_cancel method to automatically cancel related manufacturing orders
        when the sales order is cancelled.
        """
        # First, call the original method to cancel the sales order and delivery orders
        res = super(SaleOrderCustom, self).action_cancel()
        
        # Find all manufacturing orders linked to this sales order
        for order in self:
            # Find manufacturing orders linked directly via 'mo_id' field
            if order.mo_id and order.mo_id.state != 'cancel':
                order.mo_id.action_cancel()
            
            # Also find manufacturing orders linked via 'sale_id' field
            # (In case there are MOs not stored in mo_id but created with a reference to this sale order)
            manufacturing_orders = self.env['mrp.production'].search([
                ('sale_id', '=', order.id),
                ('state', 'not in', ['done', 'cancel'])  # Don't try to cancel completed orders
            ])
            
            # Cancel all found manufacturing orders that aren't already cancelled
            if manufacturing_orders:
                for mo in manufacturing_orders:
                    mo.action_cancel()
        
        return res

            
# Class khusus buat handle Down Payment
class SaleAdvancePaymentInv(models.TransientModel):
    """
    Class ini buat custom-in wizard Down Payment.
    Nambahin fitur:
    - Nominal DP yang dihitung otomatis
    - Pilihan fixed amount
    """
    _inherit = 'sale.advance.payment.inv'
    
    # Tambahkan field untuk menyimpan sale_order_id
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        default=lambda self: self._context.get('active_id', False)
    )
    
    delivery_order_id = fields.Many2one(
        'stock.picking',
        string="Delivery Order",
        help="Select the delivery order related to this sale order.",
        domain="[('sale_id', '=', sale_order_id)]"  # Gunakan sale_order_id sebagai domain
    )
    
    delivery_quantity = fields.Float(
        string="Delivery Quantity",
        compute="_compute_delivery_quantity",
        help="Total quantity from selected delivery order"
    )

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
    # Ubah field has_previous_dp agar tidak menggunakan default=True
    has_previous_dp = fields.Boolean(
        string="Has Previous Down Payment",
        compute="_compute_has_previous_dp",
        store=True  # Simpan nilai hasil compute
    )

    original_dp_percentage = fields.Float(
        string="Original Down Payment Percentage",
        compute="_compute_original_dp_percentage",
        store=True
    )

    final_payment_percentage = fields.Float(
        string="Final Payment Percentage",
        default=10.0,  # Default ke 10%
    )
    
    # Field baru untuk fixed amount di Skenario B
    original_fixed_amount = fields.Float(
        string="Original Fixed Amount",
        compute="_compute_original_fixed_amount",
        store=True,
        help="Original fixed amount from previous down payment"
    )
    
    @api.depends('sale_order_id', 'has_previous_dp')
    def _compute_original_fixed_amount(self):
        """
        Ambil nilai fixed amount yang sudah dibuat sebelumnya
        """
        for record in self:
            if record.sale_order_id and record.has_previous_dp:
                # Cari invoice down payment sebelumnya
                dp_invoices = record.sale_order_id.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted'
                )
                
                if dp_invoices:
                    # Ambil nilai nominal dari invoice pertama sebagai contoh
                    # Sesuaikan dengan struktur data Anda
                    record.original_fixed_amount = sum(dp_invoices.mapped('amount_total'))
                else:
                    record.original_fixed_amount = 0.0
            else:
                record.original_fixed_amount = 0.0

    @api.depends('sale_order_id')
    def _compute_has_previous_dp(self):
        for record in self:
            sale_order = record.sale_order_id
            if sale_order:
                # Logika sederhana: jika sudah ada invoice yang diposting, maka ini adalah Skenario B
                has_previous_invoice = bool(sale_order.invoice_ids.filtered(lambda inv: inv.state == 'posted'))
                record.has_previous_dp = has_previous_invoice
                _logger.info(f"has_previous_dp for order {sale_order.name}: {record.has_previous_dp}")
            else:
                record.has_previous_dp = False

    @api.depends('sale_order_id')
    def _compute_original_dp_percentage(self):
        """
        Ambil nilai persentase DP yang sudah dibuat sebelumnya
        """
        for record in self:
            if record.sale_order_id and record.has_previous_dp:
                # Ambil dari sale_order.down_payment_percentage
                record.original_dp_percentage = record.sale_order_id.down_payment_percentage
            else:
                record.original_dp_percentage = 0.0

    @api.onchange('final_payment_percentage')
    def _onchange_final_payment_percentage(self):
        """
        Update nominal berdasarkan persentase final yang dimasukkan
        """
        if self.advance_payment_method == 'percentage' and self.has_previous_dp:
            sale_order = self.sale_order_id
            if sale_order:
                price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
                # Hitung nominal berdasarkan persentase final
                self.nominal = (price_subtotal * self.final_payment_percentage) / 100
                
                # Override nilai amount (persentase) yang akan digunakan oleh metode standar
                self.amount = self.final_payment_percentage

    def _compute_advance_payment_method_selection(self):
        """
        Function ini buat ngatur pilihan metode pembayaran:
        - Regular invoice (bayar full)
        - Down payment pake persentase
        - Fixed amount (nominal tetap)
        - Based on delivery (berdasarkan pengiriman)
        """
        selection = [
            ('percentage', 'Percentage'),     # DP pake persentase
            ('fixed', 'Fixed amount'),        # DP pake nominal tetap
            ('delivery', 'Based on Delivery') # Berdasarkan pengiriman
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
            
            # Hitung total yang udah dibayar - HANYA invoice dengan status 'posted'
            amount_invoiced = sum(
                invoice.amount_total 
                for invoice in sale_order.invoice_ids 
                if invoice.state == 'posted'
            )
        
            # Hitung total yang harus dibayar (amount to invoice)
            # amount_to_invoice = sale_order.hpp_total - amount_invoiced
            # PERBAIKAN: Gunakan price_subtotal dari order lines
            price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
            amount_to_invoice = price_subtotal - amount_invoiced

            if self.advance_payment_method == 'percentage':
                # Hitung nominal berdasarkan persentase yang baru
                self.nominal = (amount_to_invoice * self.amount) / 100
                self.amount_to_invoice = amount_to_invoice

    # Function yang dipanggil waktu metode pembayaran berubah
    @api.onchange('advance_payment_method') 
    def _onchange_advance_payment_method(self):
        """
        Function untuk menghitung nominal berdasarkan metode pembayaran:
        - percentage: (amount_to_invoice * amount / 100)
        - fixed: menggunakan fixed_amount yang diinput user
        - delivery: berdasarkan pengiriman
        """
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(sale_order_id)
            
            # Ambil price_subtotal dari sale order line
            self.price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
            
            # Hitung total yang udah dibayar - HANYA dari invoice dengan status 'posted'
            amount_invoiced = sum(
                invoice.amount_total 
                for invoice in sale_order.invoice_ids 
                if invoice.state == 'posted'
            )
            
            # Hitung total yang harus dibayar
            amount_to_invoice = self.price_subtotal - amount_invoiced
            
            # Pastikan tidak negatif
            amount_to_invoice = max(0.0, amount_to_invoice)
            
            if self.advance_payment_method == 'percentage':
                # Cek apakah skenario A atau B
                if self.has_previous_dp:
                    # Skenario B: Sudah ada invoice sebelumnya
                    # Gunakan final_payment_percentage
                    self.amount = self.final_payment_percentage
                    self.nominal = (self.price_subtotal * self.final_payment_percentage) / 100
                else:
                    # Skenario A: Belum ada invoice sebelumnya
                    # Gunakan down_payment_percentage dari sale order
                    self.amount = sale_order.down_payment_percentage
                    self.nominal = (self.price_subtotal * self.amount) / 100
                
                self.amount_to_invoice = amount_to_invoice
            
            elif self.advance_payment_method == 'fixed':
                # Reset percentage amount
                self.amount = 0.0
                # Perbaikan: gunakan seluruh price_subtotal sebagai max_nominal untuk DP
                self.max_nominal = self.price_subtotal
                self.amount_to_invoice = amount_to_invoice
                self.fixed_amount = self.nominal
                
                # Cek apakah skenario A atau B
                if self.has_previous_dp:
                    # Skenario B: Sudah ada invoice sebelumnya
                    # Set default value for input_fixed_nominal jika belum diisi
                    if not self.input_fixed_nominal:
                        # Default 50% dari remaining amount sebagai contoh, atau tetapkan ke nominal lain
                        self.input_fixed_nominal = min(amount_to_invoice, self.price_subtotal * 0.5)
                    
                    # Penting: Pastikan nominal = input_fixed_nominal, bukan self.fixed_amount
                    self.nominal = self.input_fixed_nominal
                    
                    # Validasi nominal yang diinput gak boleh lebih dari total price
                    if self.input_fixed_nominal > self.price_subtotal:
                        self.input_fixed_nominal = self.price_subtotal
                        self.nominal = self.price_subtotal
                        return {
                            'warning': {
                                'title': 'Warning',
                                'message': f'Maximum allowed amount is {self.price_subtotal}'
                            }
                        }
                else:
                    # Skenario A: Fixed amount
                    self.nominal = self.fixed_amount or 0.0
                    if self.fixed_amount > self.price_subtotal:
                        return {
                            'warning': {
                                'title': 'Warning',
                                'message': f'Maximum allowed amount is {self.price_subtotal}'
                            }
                        }
                    
            elif self.advance_payment_method == 'delivery':
                # Fetch delivery orders related to the sale order
                delivery_orders = self.env['stock.picking'].search([
                    ('sale_id', '=', sale_order.id),
                    ('state', '!=', 'cancel')  # Exclude cancelled deliveries
                ])
                # Set default delivery order if exists
                self.delivery_order_id = delivery_orders and delivery_orders[0].id or False
                
                # Calculate amount based on selected delivery order
                if self.delivery_order_id:
                    delivered_amount = sum(
                        move.sale_line_id.price_unit * move.quantity 
                        for move in self.delivery_order_id.move_ids_without_package
                    )
                    # Batasi nominal tidak boleh lebih dari amount_to_invoice
                    self.nominal = min(delivered_amount, amount_to_invoice)
                    self.amount = 100
                    self.amount_to_invoice = amount_to_invoice
                    
                    # Check if there are previous payments and compare amounts
                    if amount_invoiced > 0:
                        if amount_to_invoice >= delivered_amount:
                            # Case 1: If there's enough remaining to invoice, use delivery amount
                            self.nominal = delivered_amount
                        else:
                            # Case 2: If delivery amount exceeds remaining, adjust by subtracting invoiced amount
                            self.nominal = max(0.0, delivered_amount - amount_invoiced)
                    else:
                        # No previous payments, use full delivered amount
                        self.nominal = delivered_amount
                    
                    self.amount = 100  # Set to 100% for full invoice of delivery
                    # Penting: amount_to_invoice harus tetap total yang belum dibayar
                    self.amount_to_invoice = amount_to_invoice

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

    # Add constraint to validate amount field
    @api.constrains('amount')
    def _check_amount_percentage(self):
        """
        Validate that amount (percentage) does not exceed 100%
        """
        for record in self:
            if record.advance_payment_method == 'percentage' and record.amount > 100:
                raise ValidationError("Down payment percentage cannot exceed 100%.")
    
    
    @api.onchange('amount') #Menghitung ulang nominal DP saat jumlah persentase berubah untuk memastikan nilai DP selalu sesuai dengan total harga produksi.
    def _onchange_amount(self):
        """
        Update nominal when amount (percentage) changes
        Validate that amount doesn't exceed 100%
        """
        if self.advance_payment_method == 'percentage' and self.amount > 100:
            self.amount = 100.0
            return {
                'warning': {
                    'title': 'Warning',
                    'message': 'Down payment percentage cannot exceed 100%. Value has been set to 100%.'
                }
            }
            
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id and self.advance_payment_method == 'percentage':
            sale_order = self.env['sale.order'].browse(sale_order_id)
            price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
            
            # Hitung nominal berdasarkan persentase dari price_subtotal
            self.nominal = (price_subtotal * self.amount) / 100
            
    @api.onchange('input_fixed_nominal')
    def _onchange_input_fixed_nominal(self):
        if self.advance_payment_method == 'fixed' and self.has_previous_dp:
            self.nominal = self.input_fixed_nominal
            # Penting: Update juga fixed_amount standar dari Odoo
            self.fixed_amount = self.input_fixed_nominal
    
    @api.onchange('delivery_order_id')
    def _onchange_delivery_order(self):
        """
        Update nominal when delivery order is selected
        """
        if self.advance_payment_method == 'delivery' and self.delivery_order_id:
            # Get the active sale order
            sale_order_id = self.env.context.get('active_id')
            if sale_order_id:
                sale_order = self.env['sale.order'].browse(sale_order_id)
                
                # Calculate invoiced amount - HANYA invoice dengan status 'posted'
                amount_invoiced = sum(
                    invoice.amount_total 
                    for invoice in sale_order.invoice_ids 
                    if invoice.state == 'posted'
                )
            
                # Calculate total amount to invoice
                amount_to_invoice = self.price_subtotal - amount_invoiced
                
                # Calculate delivered amount
                delivered_amount = sum(
                    move.sale_line_id.price_unit * move.quantity 
                    for move in self.delivery_order_id.move_ids_without_package
                )
                # Batasi nominal tidak boleh lebih dari amount_to_invoice
                if delivered_amount > amount_to_invoice:
                    self.nominal = amount_to_invoice
                else:
                    self.nominal = delivered_amount
                
                # Jika nominal masih 0, pastikan nominal diisi dengan amount_to_invoice
                if self.nominal <= 0 and amount_to_invoice > 0:
                    self.nominal = amount_to_invoice
                
                # Apply the same logic as in _onchange_advance_payment_method
                # if amount_invoiced > 0:
                #     if amount_to_invoice >= delivered_amount:
                #         self.nominal = delivered_amount
                #     else:
                #         self.nominal = max(0.0, delivered_amount - amount_invoiced)
                # else:
                #     self.nominal = delivered_amount

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
            
            # Hitung total yang udah dibayar - HANYA dari invoice dengan status 'posted'
            amount_invoiced = sum(
                invoice.amount_total 
                for invoice in sale_order.invoice_ids 
                if invoice.state == 'posted'
            )
            
            # Hitung total yang harus dibayar
            amount_to_invoice = price_subtotal - amount_invoiced
            
            # Check if the order is fully paid (within a small rounding error)
            is_fully_paid = (amount_to_invoice <= 0.01)
            
            if is_fully_paid:
                # Raise warning if the order is already fully paid
                raise UserError(_("This order is already fully invoiced. No more invoices can be created."))
            
            
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

    @api.depends('delivery_order_id')
    def _compute_delivery_quantity(self):
        """
        Compute total quantity from selected delivery order
        """
        for record in self:
            if record.delivery_order_id:
                record.delivery_quantity = sum(
                    move.quantity 
                    for move in record.delivery_order_id.move_ids_without_package
                )
            else:
                record.delivery_quantity = 0.0
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

    @api.depends('delivery_order_id')
    def _compute_delivery_quantity(self):
        """
        Compute total quantity from selected delivery order
        """
        for record in self:
            if record.delivery_order_id:
                record.delivery_quantity = sum(
                    move.quantity 
                    for move in record.delivery_order_id.move_ids_without_package
                )
            else:
                record.delivery_quantity = 0.0
                
    def _create_invoices(self, sale_orders):
        """
        Override method _create_invoices untuk custom invoice berdasarkan delivery
        """
        # Don't call super() here for fixed amount with previous DP
        if self.advance_payment_method == 'fixed' and self.has_previous_dp:
            # Call super() with the modified context
            invoices = super(SaleAdvancePaymentInv, self.with_context(
                default_invoice_amount=self.input_fixed_nominal
            ))._create_invoices(sale_orders)
        else:
            # For all other cases, call super() normally
            invoices = super()._create_invoices(sale_orders)
        
        if self.advance_payment_method == 'delivery' and self.delivery_order_id:
            # Update the sale order line name for delivery-based invoice
            for sale_order in sale_orders:
                # Find the down payment line that was just created
                dp_lines = sale_order.order_line.filtered(
                    lambda l: l.name and 'Down Payment' in l.name and '(Draft)' in l.name
                )
                if dp_lines:
                    # Get the most recent one
                    dp_line = dp_lines[-1]
                    # Extract date
                    import re
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', dp_line.name)
                    date_part = date_match.group(1) if date_match else fields.Date.today().strftime('%m/%d/%Y')
                    
                    # Change to Based On Delivery format
                    dp_line.name = f"Based On Delivery {date_part} (Draft)"
            
            # Continue with the rest of the delivery invoice processing...
            invoice_amount = self.env.context.get('default_invoice_amount', self.nominal)

            if not invoice_amount or invoice_amount == 0:
                sale_order_id = self.env.context.get('active_id')
                if sale_order_id and self.delivery_order_id:
                    sale_order = self.env['sale.order'].browse(sale_order_id)
                    # Hitung total yang udah dibayar - HANYA dari invoice dengan status 'posted'
                    amount_invoiced = sum(
                        invoice.amount_total 
                        for invoice in sale_order.invoice_ids 
                        if invoice.state == 'posted'
                    )
                    price_subtotal = sum(sale_order.order_line.mapped('price_subtotal'))
                    amount_to_invoice = price_subtotal - amount_invoiced

                    delivered_amount = sum(
                        move.sale_line_id.price_unit * move.quantity
                        for move in self.delivery_order_id.move_ids_without_package
                    )

                    invoice_amount = min(delivered_amount, amount_to_invoice)

                    if amount_invoiced > 0:
                        if amount_to_invoice >= delivered_amount:
                            invoice_amount = delivered_amount
                        else:
                            invoice_amount = max(0.0, delivered_amount - amount_invoiced)
                    else:
                        invoice_amount = delivered_amount

            for invoice in invoices:
                sale_order_id = invoice.invoice_origin and self.env['sale.order'].search([
                    ('name', '=', invoice.invoice_origin)
                ], limit=1)

                invoice.invoice_line_ids.unlink()
                invoice_line_data = {}

                for move in self.delivery_order_id.move_ids_without_package:
                    sale_line = move.sale_line_id
                    if not sale_line:
                        continue

                    quantity = move.quantity if move.quantity > 0 else 1.0
                    # Gunakan price_unit asli dari sales order line
                    price_unit = sale_line.price_unit
                    
                    invoice_line = self.env['account.move.line'].create({
                        'move_id': invoice.id,
                        'product_id': move.product_id.id,
                        'name': move.product_id.name,
                        'price_unit': price_unit,
                        'quantity': quantity,
                        'delivery_quantity': quantity,
                        'product_uom_id': move.product_uom.id,
                        'tax_ids': [(6, 0, sale_line.tax_id.ids)],
                        'account_id': move.product_id.property_account_income_id.id or
                                    move.product_id.categ_id.property_account_income_categ_id.id,
                    })

                    invoice_line_data[sale_line.id] = invoice_line.id

                invoice._compute_amount()

                # Temukan baris draft (qty 0 & price 0) untuk update
                if sale_order_id:
                    draft_lines = sale_order_id.order_line.filtered(
                        lambda l: l.qty_invoiced == 0 and l.price_unit == 0.0
                    )
                    if draft_lines:
                        draft_line = draft_lines[-1]  # Ambil baris paling akhir
                        
                        # PERBAIKAN: Alih-alih menggunakan price_unit asli, gunakan amount_to_invoice
                        # amount_to_invoice sudah merupakan total yang tersisa setelah dikurangi selisih
                        
                        # Set qty_invoiced = 1.0 (untuk tracking Odoo)
                        # Dan price_unit = amount_to_invoice (total yang sudah dikurangi selisih)
                        draft_line.write({
                            'qty_invoiced': 1.0,
                            'price_unit': invoice_amount,  # Gunakan amount_to_invoice yang sudah dikurangi selisih
                        })
                        
                        # Update langsung ke database untuk memastikan perubahan tersimpan
                        self.env.cr.execute("""
                            UPDATE sale_order_line 
                            SET qty_invoiced = %s,
                                price_unit = %s
                            WHERE id = %s
                        """, (
                            1.0,
                            amount_to_invoice,  # Gunakan amount_to_invoice alih-alih original_price_unit
                            draft_line.id
                        ))
                        draft_line.invalidate_recordset(['qty_invoiced', 'price_unit'])
                    else:
                        # Fallback ke price_unit dari account.move.line pertama jika tidak ada draft line
                        first_line = invoice.invoice_line_ids.filtered(lambda l: not l.display_type and l.price_unit > 0)
                        if first_line:
                            # Tetap gunakan amount_to_invoice untuk fallback ini juga
                            sale_order_id.write({
                                'order_line': [(0, 0, {
                                    'name': f"Based On Delivery {fields.Date.today().strftime('%m/%d/%Y')} (Draft)",
                                    'qty_invoiced': 1.0,
                                    'price_unit': amount_to_invoice,
                                    'product_uom_qty': 1.0,
                                    'product_id': first_line[0].product_id.id or False,
                                })]
                            })

                # Hubungkan invoice line ke sale_line jika belum ada
                if sale_order_id:
                    for line in invoice.invoice_line_ids:
                        if not line.sale_line_ids:
                            sale_line = sale_order_id.order_line.filtered(
                                lambda l: l.product_id.id == line.product_id.id
                            )
                            if sale_line:
                                line.sale_line_ids = [(6, 0, [sale_line[0].id])]
                
                # Jika total invoice melebihi jumlah yang tersisa untuk ditagih, tambahkan baris potongan
                if invoice.amount_total > amount_to_invoice:
                    # Hitung selisih yang perlu disesuaikan
                    selisih = invoice.amount_total - amount_to_invoice
                    
                    # Format persentase DP untuk ditampilkan
                    dp_percentage = sale_order_id.down_payment_percentage if sale_order_id else 0
                    
                    # Jumlah invoice yang sudah ada sebelumnya
                    previous_invoices_count = len(sale_order_id.invoice_ids.filtered(lambda i: i.state == 'posted'))
                    
                    # Tambahkan section header 
                    section_line = self.env['account.move.line'].create({
                        'move_id': invoice.id,
                        'name': "Payment Summary",
                        'display_type': 'line_section',
                        'account_id': invoice.invoice_line_ids[0].account_id.id if invoice.invoice_line_ids else False,
                    })

                    # Buat baris baru untuk potongan dengan penjelasan detail
                    adjustment_line = self.env['account.move.line'].create({
                        'move_id': invoice.id,
                        'name': f"Adjustment for previous payments (Down Payment {dp_percentage}% + {previous_invoices_count} previous invoice(s) - DO#{self.delivery_order_id.name})",
                        'price_unit': -selisih,  # Nilai negatif untuk mengurangi
                        'quantity': 1.0,
                        'product_uom_id': invoice.invoice_line_ids[0].product_uom_id.id if invoice.invoice_line_ids else False,
                        'account_id': invoice.invoice_line_ids[0].account_id.id if invoice.invoice_line_ids else False,
                    })

                    # Tambah penjelasan detail
                    detail_line = self.env['account.move.line'].create({
                        'move_id': invoice.id,
                        'name': f"This invoice reflects delivery of {self.delivery_quantity} units while maintaining original unit price. "
                            f"A {selisih:,.2f} adjustment has been applied based on previous payments totaling {amount_invoiced:,.2f} "
                            f"from the overall order value of {price_subtotal:,.2f}.",
                        'quantity': 0,
                        'price_unit': 0,
                        'account_id': invoice.invoice_line_ids[0].account_id.id if invoice.invoice_line_ids else False,
                        'display_type': 'line_note',
                    })
                    
                    # Pastikan perhitungan ulang dilakukan
                    invoice._compute_amount()
                    
                    # Final check - if we're still off by a small amount, add a rounding adjustment
                    if abs(invoice.amount_total - amount_to_invoice) > 0.01:
                        final_diff = amount_to_invoice - invoice.amount_total
                        
                        rounding_line = self.env['account.move.line'].create({
                            'move_id': invoice.id,
                            'name': "Rounding adjustment",
                            'price_unit': final_diff,
                            'quantity': 1.0,
                            'account_id': invoice.invoice_line_ids[0].account_id.id if invoice.invoice_line_ids else False,
                            'product_uom_id': invoice.invoice_line_ids[0].product_uom_id.id if invoice.invoice_line_ids else False,
                        })
                        
                        # Recalculate totals
                        invoice._compute_amount()
                
                # Set price_subtotal secara langsung jika masih diperlukan
                # Ini metode terakhir jika cara di atas belum menghasilkan nilai yang tepat
                if abs(invoice.amount_total - amount_to_invoice) > 0.01:
                    # Update nilai di database langsung
                    self.env.cr.execute("""
                        UPDATE account_move
                        SET amount_total = %s,
                            amount_untaxed = %s,
                            amount_residual = %s,
                            amount_residual_signed = %s
                        WHERE id = %s
                    """, (
                        amount_to_invoice,
                        amount_to_invoice,  # Jika tidak ada pajak
                        amount_to_invoice,  # Jumlah yang harus dibayar
                        amount_to_invoice if invoice.move_type == 'out_invoice' else -amount_to_invoice,  # Signed residual
                        invoice.id
                    ))
                    # Invalidate cache untuk memaksa reload nilai dari database
                    invoice.invalidate_recordset(['amount_total', 'amount_untaxed', 'amount_residual', 'amount_residual_signed'])

        return invoices
    
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    delivery_quantity = fields.Float(
        string="Delivery Quantity",
        help="Quantity from delivery order"
    )
    
    
class AccountMove(models.Model):
    _inherit = 'account.move'

    # First, add the missing field definition
    was_cancelled = fields.Boolean(
        string="Was Previously Cancelled",
        default=False,
        help="Technical field to track if an invoice was previously cancelled"
    )
    
    remaining_amount = fields.Monetary(
        string="Remaining Amount",
        compute="_compute_remaining_amount",
        store=True,
        help="Amount to be paid after deducting the down payment."
    )
    
    @api.depends('amount_total', 'invoice_line_ids', 'payment_state')
    def _compute_remaining_amount(self):
        for record in self:
            # Calculate down payment amount (lines with 'down payment' in name)
            down_payment = sum(
                line.price_subtotal for line in record.invoice_line_ids 
                if line.name and isinstance(line.name, str) and 'down payment' in line.name.lower()
            )
            
            # Calculate amount from delivery-based invoices (lines with delivery_quantity > 0)
            delivery_based_amount = sum(
                line.price_subtotal for line in record.invoice_line_ids
                if line.delivery_quantity > 0
            )
            
            # Check if this is a paid invoice
            is_paid = record.payment_state in ['paid', 'partial']
            
            # All paid amounts and down payments should be deducted
            total_deductions = down_payment + delivery_based_amount if is_paid else down_payment
            
            record.remaining_amount = record.amount_total - total_deductions
            
    
    
    def _track_previously_cancelled_invoices(self):
        """Store which invoices were in cancelled state before state change"""
        for invoice in self:
            if invoice.state == 'cancel':
                # Using direct assign instead of write() to avoid triggering field recomputation
                invoice.was_cancelled = True


    def button_draft(self):
        """Override button_draft to maintain special handling for cancelled invoices"""
        # Store which invoices were in cancelled state before going to draft
        self._track_previously_cancelled_invoices()
        
        # Update related sale order lines before changing the invoice state
        for invoice in self:
            # Handle both cancelled and posted invoices
            if invoice.move_type in ('out_invoice', 'out_refund'):
                # Check if this is a delivery-based invoice
                is_delivery_based = any(
                    hasattr(line, 'delivery_quantity') and line.delivery_quantity > 0
                    for line in invoice.invoice_line_ids
                )
                
                # Find all related sale order lines
                related_sale_lines = self.env['sale.order.line']
                
                # Method 1: Through invoice_lines relationship
                for inv_line in invoice.invoice_line_ids:
                    if inv_line.sale_line_ids:
                        related_sale_lines |= inv_line.sale_line_ids
                
                # Method 2: Look for sale order lines referencing this invoice in their name
                if invoice.name:
                    name_pattern = invoice.name
                    sale_lines_by_name = self.env['sale.order.line'].search([
                        ('name', 'like', name_pattern),
                        ('display_type', '=', False)
                    ])
                    related_sale_lines |= sale_lines_by_name
                
                # Method 3: For down payments specifically
                down_payment_lines = self.env['sale.order.line'].search([
                    ('name', 'like', 'Down Payment:'),
                    ('order_id.invoice_ids', 'in', invoice.ids)
                ])
                related_sale_lines |= down_payment_lines
                
                # Method 4: For delivery-based invoices specifically
                if invoice.state == 'posted':
                    delivery_lines = self.env['sale.order.line'].search([
                        ('name', 'like', 'Based On Delivery'),
                        ('order_id.invoice_ids', 'in', invoice.ids)
                    ])
                    related_sale_lines |= delivery_lines
                
                # Update sale order line descriptions based on current invoice state
                for sale_line in related_sale_lines:
                    if invoice.state == 'cancel' and sale_line.name:
                        # For cancelled invoices
                        new_name = sale_line.name.replace(' [CANCELLED]', '')
                        new_name = new_name.replace('(Cancelled)', '(Draft)')
                        sale_line.name = new_name
                    elif invoice.state == 'posted' and sale_line.name:
                        # For posted invoices going to draft
                        if 'Based On Delivery' in sale_line.name and '(Posted)' in sale_line.name:
                            # Keep as Based On Delivery for delivery-based invoices
                            new_name = sale_line.name.replace('(Posted)', '(Draft)')
                            sale_line.name = new_name
                        elif 'Down Payment' in sale_line.name and '(ref:' in sale_line.name:
                            # Extract date from the ref format
                            import re
                            date_match = re.search(r'on (\d{2}/\d{2}/\d{4})', sale_line.name)
                            date_part = date_match.group(1) if date_match else ""
                            
                            # Check if it has Fixed suffix
                            is_fixed = ' - Fixed' in sale_line.name
                            suffix = ' - Fixed' if is_fixed else ''
                            
                            # Change back to draft format
                            new_name = f"Down Payment: {date_part} (Draft){suffix}"
                            sale_line.name = new_name
        
        # Call the original method to complete the draft process
        return super(AccountMove, self).button_draft()
    
    def button_cancel(self):
        """Override button_cancel to update sale order lines when invoice is cancelled"""
        # Call the original method first to ensure the invoice is properly cancelled
        result = super(AccountMove, self).button_cancel()
        
        # Now update the related sale order lines
        for invoice in self:
            # Only process if this is a customer invoice
            if invoice.move_type in ('out_invoice', 'out_refund'):
                # Check if this is a delivery-based invoice
                is_delivery_based = any(
                    hasattr(line, 'delivery_quantity') and line.delivery_quantity > 0
                    for line in invoice.invoice_line_ids
                )
                
                # Find all related sale order lines
                related_sale_lines = self.env['sale.order.line']
                
                # Method 1: Through invoice_lines relationship
                for inv_line in invoice.invoice_line_ids:
                    if inv_line.sale_line_ids:
                        related_sale_lines |= inv_line.sale_line_ids
                
                # Method 2: Look for sale order lines referencing this invoice in their name
                if invoice.name:
                    name_pattern = invoice.name
                    sale_lines_by_name = self.env['sale.order.line'].search([
                        ('name', 'like', name_pattern),
                        ('display_type', '=', False)
                    ])
                    related_sale_lines |= sale_lines_by_name
                
                # Method 3: For down payments and delivery-based specifically
                payment_lines = self.env['sale.order.line'].search([
                    '|',
                    ('name', 'like', 'Down Payment:'),
                    ('name', 'like', 'Based On Delivery'),
                    ('order_id.invoice_ids', 'in', invoice.ids)
                ])
                related_sale_lines |= payment_lines
                
                # Update sale order line descriptions
                for sale_line in related_sale_lines:
                    if sale_line.name and '(Draft)' in sale_line.name:
                        # Simply replace Draft with Cancelled, no extra tags
                        new_name = sale_line.name.replace('(Draft)', '(Cancelled)')
                        sale_line.name = new_name
        
        return result
    
    def action_post(self):
        """Override action_post to update sale order lines when invoice is posted"""
        # Call the original method first to ensure the invoice is properly posted
        result = super(AccountMove, self).action_post()
        
        # Now update the related sale order lines
        for invoice in self:
            # Only process if this is a customer invoice
            if invoice.move_type in ('out_invoice', 'out_refund'):
                # Check if this invoice was created from delivery-based method
                is_delivery_based = any(
                    hasattr(line, 'delivery_quantity') and line.delivery_quantity > 0
                    for line in invoice.invoice_line_ids
                )
                
                # Find all related sale order lines
                related_sale_lines = self.env['sale.order.line']
                
                # Method 1: Through invoice_lines relationship
                for inv_line in invoice.invoice_line_ids:
                    if inv_line.sale_line_ids:
                        related_sale_lines |= inv_line.sale_line_ids
                
                # Method 2: Look for sale order lines referencing this invoice in their name
                if invoice.name:
                    name_pattern = invoice.name
                    sale_lines_by_name = self.env['sale.order.line'].search([
                        ('name', 'like', name_pattern),
                        ('display_type', '=', False)
                    ])
                    related_sale_lines |= sale_lines_by_name
                
                # Method 3: For down payments and delivery-based specifically
                payment_lines = self.env['sale.order.line'].search([
                    '|',
                    ('name', 'like', 'Down Payment:'),
                    ('name', 'like', 'Based On Delivery'),
                    ('order_id.invoice_ids', 'in', invoice.ids)
                ])
                related_sale_lines |= payment_lines
                
                # Update sale order line descriptions
                for sale_line in related_sale_lines:
                    if sale_line.name and '(Draft)' in sale_line.name:
                        # Extract the date part if it exists
                        import re
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', sale_line.name)
                        date_part = date_match.group(1) if date_match else fields.Date.today().strftime('%m/%d/%Y')
                        
                        if 'Based On Delivery' in sale_line.name:
                            # For delivery-based invoices, just change to Posted
                            new_name = sale_line.name.replace('(Draft)', '(Posted)')
                        else:
                            # For down payments, use the ref format
                            # Check if it has Fixed suffix
                            is_fixed = ' - Fixed' in sale_line.name
                            suffix = ' - Fixed' if is_fixed else ''
                            
                            # Create the ref format
                            new_name = f"Down Payment (ref: {invoice.name} on {date_part}){suffix}"
                        
                        sale_line.name = new_name
        
        return result
    
    def unlink(self):
        """Override unlink to remove related sale order lines when invoice is deleted"""
        # Find related sale order lines before deleting the invoice
        lines_to_delete = self.env['sale.order.line']
        
        for invoice in self:
            # Only process if this is a customer invoice
            if invoice.state == 'draft' and invoice.move_type in ('out_invoice', 'out_refund'):
                # Method 1: Check invoice lines with delivery_quantity
                delivery_based = False
                for inv_line in invoice.invoice_line_ids:
                    if hasattr(inv_line, 'delivery_quantity') and inv_line.delivery_quantity > 0:
                        delivery_based = True
                        if inv_line.sale_line_ids:
                            lines_to_delete |= inv_line.sale_line_ids
                
                # Method 2: Look for sale order lines referencing this invoice in their name
                if invoice.name:
                    name_pattern = invoice.name
                    sale_lines_by_name = self.env['sale.order.line'].search([
                        ('name', 'like', name_pattern),
                        ('display_type', '=', False),
                    ])
                    lines_to_delete |= sale_lines_by_name
                
                # Method 3: Check via invoice origin
                if invoice.invoice_origin:
                    sale_order = self.env['sale.order'].search([
                        ('name', '=', invoice.invoice_origin)
                    ], limit=1)
                    
                    if sale_order:
                        if delivery_based:
                            # For delivery-based invoices, find newly created delivery lines
                            delivery_lines = sale_order.order_line.filtered(
                                lambda l: l.name and 
                                (('Based On Delivery' in l.name) or 
                                ('Down Payment' in l.name and invoice.name and invoice.name in l.name))
                            )
                            lines_to_delete |= delivery_lines
                        else:
                            # For regular down payments
                            down_payment_lines = sale_order.order_line.filtered(
                                lambda l: l.name and 'Down Payment' in l.name and 
                                invoice.name and invoice.name in l.name
                            )
                            lines_to_delete |= down_payment_lines
        
        # Call the original unlink method to delete the invoices
        result = super(AccountMove, self).unlink()
        
        # Now delete the sale order lines
        if lines_to_delete:
            # Add logging to see what's being deleted
            _logger.info(f"Deleting sale order lines: {lines_to_delete.mapped('name')}")
            
            # Use a protection to avoid errors if some lines are already deleted
            existing_lines = lines_to_delete.exists()
            if existing_lines:
                existing_lines.unlink()
        
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    remaining_qty = fields.Float(
        string="Remaining Qty",
        compute="_compute_remaining_qty",
        store=True,
        help="Quantity that still needs to be delivered"
    )
    
    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_remaining_qty(self):
        for line in self:
            line.remaining_qty = line.product_uom_qty - line.qty_delivered