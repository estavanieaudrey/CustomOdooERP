from odoo import models, fields, api


# Class untuk nambahin fitur custom di product template
class ProductCustom(models.Model):
    _inherit = "product.template"  # Inherit dari product.template bawaan Odoo

    # Field buat nentuin tipe kertas/material
    # Ini penting buat ngitung quantity di BOM lines
    tipe_kertas = fields.Selection([
        ('a4', 'A4'),               # Kertas ukuran A4
        ('b5', 'B5'),               # Kertas ukuran B5
        ('isi', 'Kertas Isi'),      # Kertas untuk isi buku
        ('cover', 'Kertas Cover'),   # Kertas untuk cover buku
        ('plate_isi', 'Plate Isi'),  # Plate cetak untuk isi
        ('plate_cover', 'Plate Cover'), # Plate cetak untuk cover
        ('box', 'Box')               # Box untuk packaging
    ], string="Tipe", default="isi")  # Default ke 'isi' kalo bikin produk baru

    # Function yang dipanggil waktu tipe_kertas berubah
    @api.onchange('tipe_kertas')
    def _onchange_tipe_kertas(self):
        """
        Update kode produk otomatis pas milih tipe kertas.
        
        Contoh:
        - Pilih tipe 'A4' -> kodenya jadi 'A4'
        - Pilih tipe 'B5' -> kodenya jadi 'B5'
        - Pilih tipe 'Kertas Isi' -> kodenya jadi 'kertas_isi'
        - Pilih tipe 'Box' -> kodenya jadi 'box'
        
        Ini berguna buat:
        1. Gampang nyari produk
        2. Gampang filter di laporan
        3. Konsistensi penamaan
        """
        if self.tipe_kertas:
            # Set default_code sesuai tipe yang dipilih
            if self.tipe_kertas == 'a4':
                self.default_code = 'A4'
            elif self.tipe_kertas == 'b5':
                self.default_code = 'B5'
            elif self.tipe_kertas == 'isi':
                self.default_code = 'kertas_isi'
            elif self.tipe_kertas == 'cover':
                self.default_code = 'kertas_cover'
            elif self.tipe_kertas == 'plate_isi':
                self.default_code = 'plate_isi'
            elif self.tipe_kertas == 'plate_cover':
                self.default_code = 'plate_cover'
            elif self.tipe_kertas == 'box':
                self.default_code = 'box'

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Update this to match exactly with the ProductCustom class
    tipe_kertas = fields.Selection([
        ('a4', 'A4'),               # Kertas ukuran A4
        ('b5', 'B5'),               # Kertas ukuran B5
        ('isi', 'Kertas Isi'),      # Kertas untuk isi buku
        ('cover', 'Kertas Cover'),   # Kertas untuk cover buku
        ('plate_isi', 'Plate Isi'),  # Plate cetak untuk isi
        ('plate_cover', 'Plate Cover'), # Plate cetak untuk cover
        ('box', 'Box')               # Box untuk packaging
    ], string='Tipe Kertas', default='isi')

    @api.onchange('tipe_kertas')
    def _onchange_tipe_kertas(self):
        """
        Update kode produk otomatis pas milih tipe kertas.
        """
        if self.tipe_kertas:
            if self.tipe_kertas == 'a4':
                self.default_code = 'A4'
            elif self.tipe_kertas == 'b5':
                self.default_code = 'B5'
            elif self.tipe_kertas == 'isi':
                self.default_code = 'kertas_isi'
            elif self.tipe_kertas == 'cover':
                self.default_code = 'kertas_cover'
            elif self.tipe_kertas == 'plate_isi':
                self.default_code = 'plate_isi'
            elif self.tipe_kertas == 'plate_cover':
                self.default_code = 'plate_cover'
            elif self.tipe_kertas == 'box':
                self.default_code = 'box'

