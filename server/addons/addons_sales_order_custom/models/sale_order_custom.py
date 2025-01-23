from odoo import models, fields, api
from odoo.exceptions import ValidationError
from io import BytesIO
import base64

class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'

    # === PASAL 2: Detail Produk ===
    # Field untuk nyimpen detail produk, kebanyakan diambil otomatis dari BoM
    detail_isi = fields.Char(
        string="Detail Isi",
        compute="_compute_detail_isi",
        store=True
    )
    detail_cover = fields.Char(
        string="Detail Cover",
        compute="_compute_detail_cover",
        store=True
    )
    detail_design = fields.Char(string="Design")
    
    # Dropdown untuk jenis jilid, diambil dari BoM
    jenis_jilid = fields.Selection([
        ('perfect_binding', 'Perfect Binding (Lem)'),
        ('stitching', 'Stitching (Kawat)')
    ], string="Jenis Jilid", compute="_compute_jenis_jilid", store=True)

    # Dropdown untuk jenis UV, diambil dari BoM
    jenis_uv = fields.Selection([
        ('glossy', 'Glossy'),
        ('matte', 'Matte (Doff)')
    ], string="Jenis UV", compute="_compute_jenis_uv", store=True)

    detail_packing = fields.Char(string="Packing", compute="_compute_detail_packing", readonly=True)
    detail_quantity = fields.Integer(related="bom_id.qty_buku", string="Quantity Buku", readonly=True)

    # === PASAL 3: Harga dan Pembayaran ===
    price_unit = fields.Float(related="order_line.price_unit", string="Unit Price", readonly=True)
    total_amount = fields.Monetary(related="amount_total", string="Total Harga", readonly=True)
    
    # Field untuk down payment
    down_payment_yes_no = fields.Boolean(string="Down Payment (Yes/No)")
    down_payment_percentage = fields.Float(string="Down Payment (%)")
    down_payment_nominal = fields.Float(string="Down Payment (Nominal)", 
                                      compute="_compute_down_payment_nominal",
                                      store=True)
    
    # Field untuk data rekening transfer
    # transfer_rekening_name = fields.Many2one('res.partner.bank', string="Nama Rekening")
    # transfer_rekening_bank = fields.Many2one('res.bank', string="Bank")
    transfer_rekening_name = fields.Char(string="Nama Rekening")
    transfer_rekening_bank = fields.Char(string="Bank")
    transfer_rekening_number = fields.Char(string="Nomor Rekening")
    transfer_rekening_branch = fields.Char(string="Cabang")

    # === PASAL 4: Expired Date dan Tanda Tangan ===
    expired_date = fields.Date(string="Expired Date")
    # customer_signature = fields.Binary(string="Tanda Tangan", attachment=True)

    # Field untuk pilih BoM yang akan dipakai sebagai sumber data
    bom_id = fields.Many2one('mrp.bom', string="Bill of Materials", help="Pilih BoM untuk mengambil data HPP.")
    
    # Field yang diambil dari BoM
    ukuran_buku = fields.Selection(related="bom_id.ukuran_buku", string="Ukuran Buku", readonly=True)
    jenis_cetakan_isi = fields.Selection(related="bom_id.jenis_cetakan_isi", string="Jenis Cetakan Isi", readonly=True)
    jenis_cetakan_cover = fields.Selection(related="bom_id.jenis_cetakan_cover", string="Jenis Cetakan Cover", readonly=True)
    jmlh_halaman_buku = fields.Integer(related="bom_id.jmlh_halaman_buku", string="Jumlah Halaman Buku", readonly=True)
    jasa_jilid = fields.Integer(related="bom_id.jasa_jilid", string="Biaya Jilid", readonly=True)
    isi_box = fields.Integer(related="bom_id.isi_box", string="Isi Box", readonly=True)
    qty_buku = fields.Integer(related="bom_id.qty_buku", readonly=True)
    hpp_per_unit = fields.Float(related="bom_id.hpp_per_unit", string="Harga Satuan", readonly=True)
    hpp_total = fields.Float(related="bom_id.hpp_total", string="Harga Total", readonly=True)
    ppn = fields.Float(related="bom_id.ppn", string="PPn", readonly=True)

    # Fields yang diambil dari BoM (sekarang integer)
    gramasi_kertas_isi = fields.Integer(related="bom_id.gramasi_kertas_isi", readonly=True)
    gramasi_kertas_cover = fields.Integer(related="bom_id.gramasi_kertas_cover", readonly=True)
    overhead_percentage = fields.Integer(related="bom_id.overhead_percentage", readonly=True)
    ppn_percentage = fields.Integer(related="bom_id.ppn_percentage", readonly=True)
    waste_percentage = fields.Integer(related="bom_id.waste_percentage", readonly=True)

    # Function untuk ngitung detail isi dari BoM
    @api.depends('bom_id.bom_line_ids')
    def _compute_detail_isi(self):
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

    # Function untuk ngitung detail cover dari BoM, mirip kayak detail_isi
    @api.depends('bom_id.bom_line_ids')
    def _compute_detail_cover(self):
        for record in self:
            if record.bom_id:
                cover_lines = record.bom_id.bom_line_ids.filtered(
                    lambda l: "Kertas Cover" in l.product_id.name
                )
                if cover_lines:
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
        Update detail_isi dan detail_cover waktu BoM berubah
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
        for record in self:
            if record.bom_id:
                # Ambil nilai jenis_jilid dari BoM
                record.jenis_uv = record.bom_id.jenis_uv
            else:
                # Default jika tidak ada BoM
                record.jenis_uv = False

    # Ngitung detail packing di isi_bos (tambahin "/box" di belakang angka)
    @api.depends('bom_id.isi_box')
    def _compute_detail_packing(self):
        for record in self:
            if record.bom_id.isi_box:
                record.detail_packing = f"{record.bom_id.isi_box} /box"
            else:
                record.detail_packing = "Tidak Ada"

    # Ngitung nominal DP dari persentase
    @api.depends('down_payment_percentage', 'hpp_total')
    def _compute_down_payment_nominal(self):
        """Hitung nominal Down Payment berdasarkan persentase."""
        for record in self:
            if record.down_payment_yes_no and record.down_payment_percentage:
                record.down_payment_nominal = (record.hpp_total * record.down_payment_percentage) / 100
            else:
                record.down_payment_nominal = 0.0

    # Update data ke order lines waktu BoM dipilih
    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        if self.bom_id:
            # Reset order lines dulu
            self.order_line = [(5, 0, 0)]

            # Tambah produk dari BoM
            product = self.bom_id.product_tmpl_id.product_variant_id
            if product:
                self.order_line = [(0, 0, {
                    'product_id': product.id, #produk terkait BoM
                    'product_uom_qty': self.bom_id.qty_buku, #Jumlah produk atribut: qty_buku
                    'price_unit': self.bom_id.hpp_per_unit, #Harga satuan
                    'name': product.name, #Nama produk
                    'tax_id': [(6, 0, [])],  # Set pajak menjadi kosong
                })]

    # Field untuk draft perjanjian
    draft_perjanjian = fields.Binary(string="Draft Perjanjian PDF")
    draft_perjanjian_name = fields.Char(string="Nama File")
    is_signed = fields.Boolean(string="Telah Ditandatangani", default=False)
    signature_date = fields.Date(string="Tanggal Tanda Tangan")

    # is_confirmed = fields.Boolean(string="Confirmed", default=False)

    # def action_convert_to_sales_order(self):
    #     """
    #     Convert draft quotation to confirmed sales order after validating the signature.
    #     """
    #     if not self.is_signed:
    #         raise ValidationError("Draft perjanjian belum ditandatangani!")
    #     self.action_confirm()  # Confirm the sales order using Odoo's built-in method
    #     self.is_confirmed = True  # Mark the sales order as confirmed

    def action_generate_pdf(self):
        """
        Function buat bikin PDF dari template report yang udah dibuat.
        Simpel sih, cuma manggil template reportnya terus dirender jadi PDF.
        """
        # Manggil template report yang udah didaftarin di XML, terus langsung dirender
        return self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian').report_action(self)

    down_payment_percentage = fields.Float(
        string="Down Payment Percentage",
        default=10.0,  # Default 10%
        help="Percentage of the down payment for the order."
    )

    down_payment_yes_no = fields.Boolean(
        string="Enable Down Payment",
        default=True,
        help="Enable or disable down payment for this sales order."
    )

    # Override Method action_confirm di sale.order: Tambahkan logika untuk menghubungkan SO dengan MO melalui field sale_id.
    def action_confirm(self):
        # Check if draft_perjanjian exists
        for order in self:
            if not order.draft_perjanjian:
                raise ValidationError("Upload Draft Perjanjian terlebih dahulu!")
                
        # Continue with existing confirmation logic
        res = super(SaleOrderCustom, self).action_confirm()
        
        # Create draft Manufacturing Order
        for order in self:
            if order.bom_id:
                mo_vals = {
                    'product_id': order.bom_id.product_tmpl_id.product_variant_id.id,
                    'product_qty': order.qty_buku,
                    'bom_id': order.bom_id.id,
                    'sale_id': order.id,
                    'date_start': fields.Datetime.now(),
                    'origin': order.name,
                    'product_uom_id': order.bom_id.product_uom_id.id,
                    'state': 'draft',  # Ensure MO is created in draft state
                }
                self.env['mrp.production'].create(mo_vals)
        return res

    @api.constrains('is_signed', 'draft_perjanjian')
    def _check_draft_perjanjian(self):
        for record in self:
            if record.is_signed and not record.draft_perjanjian:
                raise ValidationError("Tidak dapat menandatangani perjanjian! Harap upload draft perjanjian terlebih dahulu.")

    @api.onchange('is_signed')
    def _onchange_is_signed(self):
        if self.is_signed:
            if not self.draft_perjanjian:
                self.is_signed = False
                return {
                    'warning': {
                        'title': 'Peringatan',
                        'message': 'Harap upload draft perjanjian terlebih dahulu sebelum menandatangani.'
                    }
                }
            self.signature_date = fields.Date.today()
        else:
            self.signature_date = False

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'
    
    # Field buat nyimpen nominal DP yang udah dihitung (readonly karena dihitung otomatis)
    nominal = fields.Float(string="Nominal", readonly=True, help="Computed Down Payment Nominal")
    input_fixed_nominal = fields.Float(string="Fixed Amount", help="Enter fixed amount for down payment")
    max_nominal = fields.Float(string="Maximum Amount", readonly=True, help="Maximum allowed amount")


    def _compute_advance_payment_method_selection(self):
        """
        Function ini buat ngatur pilihan metode pembayaran:
        - Regular invoice (bayar full)
        - Down payment pake persentase
        - Fixed amount (nominal tetap)
        """
        selection = [
            ('all', 'Regular invoice'),
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed amount')
        ]
        return selection

    advance_payment_method = fields.Selection(
        selection=_compute_advance_payment_method_selection,
        string='Create Invoice',
        default='all',
        required=True,
    )
    
    @api.onchange('amount')
    def _onchange_amount(self):
        """
        Update down_payment_percentage di sale order dan hitung ulang nominal
        ketika amount (percentage) berubah
        """
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id and self.advance_payment_method == 'percentage':
            sale_order = self.env['sale.order'].browse(sale_order_id)
            # Update down_payment_percentage di sale order
            sale_order.write({'down_payment_percentage': self.amount})
            
            # # Hitung ulang nominal
            # amount_invoiced = sum(sale_order.invoice_ids.mapped('amount_total'))
            # if sale_order.invoice_ids:
            #     total_max_pay = sale_order.hpp_total - amount_invoiced
            #     self.nominal = (total_max_pay * self.amount) / 100
            # else:
            #     self.nominal = (sale_order.hpp_total * self.amount) / 100


    @api.onchange('advance_payment_method') 
    def _onchange_advance_payment_method(self):
        """
        Function untuk menghitung nominal berdasarkan metode pembayaran:
        - all: hpp_total - amount_invoiced
        - percentage: (hpp_total * down_payment_percentage / 100) - amount_invoiced
        - fixed: menggunakan fixed_amount yang diinput user
        """
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(sale_order_id)
            amount_invoiced = sum(sale_order.invoice_ids.mapped('amount_total'))

            if self.advance_payment_method == 'all':
                # Regular invoice: hpp_total - amount_invoiced
                self.nominal = sale_order.hpp_total - amount_invoiced
                self.amount = 0.0
                # self.amount_to_invoice = self.nominal
            
            elif self.advance_payment_method == 'percentage':
                # Down payment dengan persentase
                self.amount = sale_order.down_payment_percentage

                # Hitung nominal DP berdasarkan persentase dari hpp_total
                if sale_order.down_payment_yes_no and sale_order.down_payment_percentage:
                    # Total yang seharusnya dibayar berdasarkan persentase
                    total_max_pay = (sale_order.hpp_total - amount_invoiced)
                    # Kurangi dengan yang sudah dibayar (amount_invoiced)
                    self.nominal = (total_max_pay * self.amount) / 100
                else:
                    self.nominal = 0.0
            
            elif self.advance_payment_method == 'fixed':
                # Fixed amount: gunakan nilai yang diinput user
                self.amount = 0.0  # Reset percentage amount
                self.max_nominal = amount_invoiced
                self.fixed_amount = self.nominal  # Gunakan nominal sebagai fixed amount
                
                if self.input_fixed_nominal:
                    if self.input_fixed_nominal > self.max_nominal:
                        return {
                            'warning': {
                                'title': 'Warning',
                                'message': f'Maximum allowed amount is {self.max_nominal}'
                            }
                        }
                    self.nominal = self.input_fixed_nominal
            # Pastikan nominal tidak negatif
            self.nominal = max(0.0, self.nominal)
            
    def action_generate_pdf(self):
        """
        Buat generate PDF dari template yang udah kita bikin
        """
        return self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian').report_action(self)

    def action_quotation_send(self):
        """
        Function buat override cara kirim quotation bawaan Odoo.
        Bedanya ini nambah attachment PDF custom kita ke emailnya.
        """
        # Panggil dulu function aslinya dari Odoo
        action = super(SaleOrderCustom, self).action_quotation_send()
        
        # Cek ada context-nya gak (buat mastiin gak error)
        if action.get('context'):
            # Bikin PDF-nya, sama kayak function di atas
            # [0] karena _render_qweb_pdf return tuple (content, type)
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
