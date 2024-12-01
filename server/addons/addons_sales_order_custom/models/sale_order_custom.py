from odoo import models, fields, api
from odoo.exceptions import ValidationError
from io import BytesIO
import base64

class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'

    # PASAL 1: Ruang Lingkup Perjanjian
    ruang_lingkup = fields.Text(string="Ruang Lingkup Perjanjian")

    # PASAL 2: Detail Produk
    # detail_ukuran = fields.Selection(related="bom_id.ukuran_buku", string="Ukuran Buku", readonly=True)
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
    jenis_jilid = fields.Selection([
        ('perfect_binding', 'Perfect Binding (Lem)'),
        ('stitching', 'Stitching (Kawat)')
    ], string="Jenis Jilid", compute="_compute_jenis_jilid", store=True)

    jenis_uv = fields.Selection([
        ('glossy', 'Glossy'),
        ('matte', 'Matte (Doff)')
    ], string="Jenis UV", compute="_compute_jenis_uv", store=True)

    detail_packing = fields.Char(string="Packing", compute="_compute_detail_packing", readonly=True)
    detail_quantity = fields.Float(related="bom_id.qty_buku", string="Quantity Buku", readonly=True)

    # PASAL 3: Harga, Down Payment, dan Rekening Transfer
    price_unit = fields.Float(related="order_line.price_unit", string="Unit Price", readonly=True)
    total_amount = fields.Monetary(related="amount_total", string="Total Harga", readonly=True)
    down_payment_yes_no = fields.Boolean(string="Down Payment (Yes/No)")
    down_payment_percentage = fields.Float(string="Down Payment (%)")
    down_payment_nominal = fields.Float(string="Down Payment (Nominal)", compute="_compute_down_payment_nominal",
                                        store=True)
    transfer_rekening_name = fields.Char(string="Nama Rekening")
    transfer_rekening_bank = fields.Char(string="Bank")
    transfer_rekening_number = fields.Char(string="Nomor Rekening")
    transfer_rekening_branch = fields.Char(string="Cabang")

    # PASAL 4: Expired Date dan Tanda Tangan
    expired_date = fields.Date(related="validity_date", string="Expired Date", readonly=True)
    customer_signature = fields.Binary(string="Tanda Tangan", attachment=True)

    # Field untuk memilih BoM
    bom_id = fields.Many2one('mrp.bom', string="Bill of Materials", help="Pilih BoM untuk mengambil data HPP.")
    # Field untuk data perjanjian
    ukuran_buku = fields.Selection(related="bom_id.ukuran_buku", string="Ukuran Buku", readonly=True)
    jenis_cetakan_isi = fields.Selection(related="bom_id.jenis_cetakan_isi", string="Jenis Cetakan Isi", readonly=True)
    jenis_cetakan_cover = fields.Selection(related="bom_id.jenis_cetakan_cover", string="Jenis Cetakan Cover", readonly=True)
    jmlh_halaman_buku = fields.Integer(related="bom_id.jmlh_halaman_buku", string="Jumlah Halaman Buku", readonly=True)
    jasa_jilid = fields.Float(related="bom_id.jasa_jilid", string="Biaya Jilid", readonly=True)
    isi_box = fields.Float(related="bom_id.isi_box", string="Isi Box (Buku/Box)", readonly=True)
    qty_buku = fields.Float(related="bom_id.qty_buku", string="Quantity Buku", readonly=True)
    hpp_per_unit = fields.Float(related="bom_id.hpp_per_unit", string="Harga Satuan", readonly=True)
    hpp_total = fields.Float(related="bom_id.hpp_total", string="Harga Total", readonly=True)
    ppn = fields.Float(related="bom_id.ppn", string="PPn", readonly=True)

    @api.depends('bom_id.bom_line_ids')
    def _compute_detail_isi(self):
        for record in self:
            if record.bom_id:
                # Filter baris dengan nama produk "Kertas Isi"
                isi_lines = record.bom_id.bom_line_ids.filtered(
                    lambda l: "Kertas Isi" in l.product_id.name
                )
                if isi_lines:
                    # Gabungkan nama produk dengan variannya
                    detail_isi_list = [
                        f"{line.product_id.name} ({', '.join(line.product_id.product_template_variant_value_ids.mapped('name'))})"
                        for line in isi_lines
                    ]
                    record.detail_isi = ", ".join(detail_isi_list)
                else:
                    record.detail_isi = "Tidak Ada"
            else:
                record.detail_isi = "Tidak Ada"

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

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """
        Ketika BoM dipilih, hitung ulang `detail_isi` dan `detail_cover`.
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

    # untuk mengambil jenis jilid dari bom
    @api.depends('bom_id.jenis_jilid')
    def _compute_jenis_jilid(self):
        for record in self:
            if record.bom_id:
                # Ambil nilai jenis_jilid dari BoM
                record.jenis_jilid = record.bom_id.jenis_jilid
            else:
                # Default jika tidak ada BoM
                record.jenis_jilid = False

    # untuk mengambil jenis uv dari bom
    @api.depends('bom_id.jenis_uv')
    def _compute_jenis_uv(self):
        for record in self:
            if record.bom_id:
                # Ambil nilai jenis_jilid dari BoM
                record.jenis_uv = record.bom_id.jenis_uv
            else:
                # Default jika tidak ada BoM
                record.jenis_uv = False

    @api.depends('bom_id.isi_box')
    def _compute_detail_packing(self):
        """Kombinasikan isi_box dengan '/box'."""
        for record in self:
            if record.bom_id.isi_box:
                record.detail_packing = f"{record.bom_id.isi_box} /box"
            else:
                record.detail_packing = "Tidak Ada"

    @api.depends('down_payment_percentage', 'hpp_total')
    def _compute_down_payment_nominal(self):
        """Hitung nominal Down Payment berdasarkan persentase."""
        for record in self:
            if record.down_payment_yes_no and record.down_payment_percentage:
                record.down_payment_nominal = (record.hpp_total * record.down_payment_percentage) / 100
            else:
                record.down_payment_nominal = 0.0

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        """
        Ketika BoM dipilih, tambahkan data ke Order Lines.
        """
        if self.bom_id:
            # Kosongkan Order Lines sebelumnya
            self.order_line = [(5, 0, 0)]

            # Tambahkan produk berdasarkan BoM
            product = self.bom_id.product_tmpl_id.product_variant_id
            if product:
                self.order_line = [(0, 0, {
                    'product_id': product.id, #produk terkait BoM
                    'product_uom_qty': self.bom_id.qty_buku, #Jumlah produk atribut: qty_buku
                    'price_unit': self.bom_id.hpp_per_unit, #Harga satuan
                    'name': product.name, #Nama produk
                    'tax_id': [(6, 0, [])],  # Set pajak menjadi kosong
                })]

    # Field tambahan untuk informasi draft
    draft_perjanjian = fields.Binary(string="Draft Perjanjian PDF")
    draft_perjanjian_name = fields.Char(string="Nama File")
    is_signed = fields.Boolean(string="Telah Ditandatangani", default=False)
    signature_date = fields.Date(string="Tanggal Tanda Tangan")

    is_confirmed = fields.Boolean(string="Confirmed", default=False)

    def action_convert_to_sales_order(self):
        """
        Convert draft quotation to confirmed sales order after validating the signature.
        """
        if not self.is_signed:
            raise ValidationError("Draft perjanjian belum ditandatangani!")
        self.action_confirm()  # Confirm the sales order using Odoo's built-in method
        self.is_confirmed = True  # Mark the sales order as confirmed

    def action_generate_pdf(self):
        # Fetch the report template
        report_template = self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian')
        if not report_template:
            raise ValueError("Template laporan tidak ditemukan.")
        return report_template.report_action(self)

        # Render the report as PDF
        report_pdf, _ = report_template._render_qweb_pdf([self.id])

        # Convert PDF content to base64
        pdf_base64 = base64.b64encode(report_pdf)

        # Create an attachment record
        attachment_values = {
            'name': "ID_Card.pdf",
            'type': 'binary',
            'datas': pdf_base64,
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': self.id,
        }
        attachment = self.env['ir.attachment'].create(attachment_values)

        # Assign the attachment to the binary field
        self.report_file = attachment.id

        return True

    down_payment_percentage = fields.Float(
        string="Down Payment Percentage",
        default=10.0,  # Default ke 10% jika belum ada
        help="Percentage of the down payment for the order."
    )

    down_payment_yes_no = fields.Boolean(
        string="Enable Down Payment",
        default=True,
        help="Enable or disable down payment for this sales order."
    )

    # Override Method action_confirm di sale.order: Tambahkan logika untuk menghubungkan SO dengan MO melalui field sale_id.
    def action_confirm(self):
        res = super(SaleOrderCustom, self).action_confirm()
        for order in self:
            if order.bom_id:
                mo_vals = {
                    'product_id': order.bom_id.product_tmpl_id.id,
                    'product_qty': order.qty_buku,
                    'bom_id': order.bom_id.id,
                    'sale_id': order.id,  # Hubungkan MO dengan SO
                    'date_planned_start': fields.Datetime.now(),
                    'origin': order.name,
                }
                self.env['mrp.production'].create(mo_vals)
        return res

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'
    nominal = fields.Float(string="Nominal", readonly=True, help="Computed Down Payment Nominal")

    def _compute_advance_payment_method_selection(self):
        """
        Remove 'fixed' option dynamically from the selection.
        """
        selection = [
            ('all', 'Regular invoice'),
            ('percentage', 'Down payment (percentage)'),
            # Do not include 'fixed' here
        ]
        return selection

    # Override the selection for advance_payment_method
    advance_payment_method = fields.Selection(
        selection=_compute_advance_payment_method_selection,
        string='Create Invoice',
        default='all',
        required=True,
    )


    @api.onchange('advance_payment_method')
    def _onchange_advance_payment_method(self):
        """
        Automatically populate 'amount' (percentage) and 'nominal' (calculated nominal)
        based on the selected sales order.
        """
        sale_order_id = self.env.context.get('active_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(sale_order_id)

            if self.advance_payment_method == 'percentage':
                # Set the percentage value (amount field)
                self.amount = sale_order.down_payment_percentage

                # Compute the nominal value
                if sale_order.down_payment_yes_no and sale_order.down_payment_percentage:
                    self.nominal = (sale_order.hpp_total * sale_order.down_payment_percentage) / 100
                else:
                    self.nominal = 0.0
            else:
                # Reset fields for "Regular Invoice"
                self.amount = 0.0
                self.nominal = 0.0


    # def action_generate_pdf(self):
    #     self.ensure_one()
    #     try:
    #         # Fetch the report using the correct report ID
    #         report = self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian')
    #
    #         # Generate the PDF content
    #         pdf_content, content_type = report.render_qweb_pdf([self.id])
    #
    #         # Convert the PDF content to Base64
    #         pdf_base64 = base64.b64encode(pdf_content)
    #
    #         # Remove any existing attachments for this record
    #         existing_attachments = self.env['ir.attachment'].search([
    #             ('res_model', '=', self._name),
    #             ('res_id', '=', self.id),
    #             ('name', '=', f"Draft_Perjanjian_{self.name}.pdf")
    #         ])
    #         existing_attachments.unlink()
    #
    #         # Save the generated PDF as an attachment
    #         attachment = self.env['ir.attachment'].create({
    #             'name': f"Draft_Perjanjian_{self.name}.pdf",
    #             'type': 'binary',
    #             'datas': pdf_base64,
    #             'res_model': self._name,
    #             'res_id': self.id,
    #             'mimetype': 'application/pdf'
    #         })
    #
    #         # Return a download link for the generated PDF
    #         return {
    #             'type': 'ir.actions.act_url',
    #             'url': f'/web/content/{attachment.id}?download=true',
    #             'target': 'self',
    #         }
    #     except Exception as e:
    #         raise ValidationError(f"Error generating PDF: {e}")

    # def action_generate_pdf(self):
    #     """
    #     Generate PDF for the custom report and return it as an action.
    #     """
    #     return self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian').report_action(self)
    #
    # def action_quotation_send(self):
    #     """
    #     Override Odoo's quotation send to include custom PDF attachment.
    #     """
    #     action = super(SaleOrderCustom, self).action_quotation_send()
    #     if action.get('context'):
    #         # Render the PDF for the current sale order
    #         pdf_content = self.env.ref('addons_sales_order_custom.action_report_draft_perjanjian')._render_qweb_pdf(self.id)[0]
    #         pdf_base64 = base64.b64encode(pdf_content)  # Convert PDF to base64
    #
    #         # Generate attachment name
    #         attachment_name = f"Quotation - {self.name or 'Draft'}.pdf"
    #
    #         # Add the attachment to the context
    #         action['context']['default_attachment_ids'] = [(0, 0, {
    #             'name': attachment_name,  # Name of the file (mandatory)
    #             'datas': pdf_base64,      # Data of the file in base64
    #             'res_model': 'sale.order',
    #             'res_id': self.id,
    #             'mimetype': 'application/pdf',
    #         })]
    #     return action
