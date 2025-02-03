from odoo import models, fields, api

from python.Lib.email.policy import default

# Class untuk nambahin fitur custom di product template
class ProductCustom(models.Model):
    _inherit = "product.template"  # Inherit dari product.template bawaan Odoo

    # Field buat nentuin tipe kertas/material
    # Ini penting buat ngitung quantity di BOM lines
    tipe_kertas = fields.Selection([
        ('isi', 'Kertas Isi'),         # Kertas untuk isi buku
        ('cover', 'Kertas Cover'),      # Kertas untuk cover buku
        ('plate_isi', 'Plate Isi'),     # Plate cetak untuk isi
        ('plate_cover', 'Plate Cover'), # Plate cetak untuk cover
        ('box', 'Box')                  # Box untuk packaging
    ], string="Tipe", default="isi")  # Default ke 'isi' kalo bikin produk baru

    # Function yang dipanggil waktu tipe_kertas berubah
    @api.onchange('tipe_kertas')
    def _onchange_tipe_kertas(self):
        """
        Update kode produk otomatis pas milih tipe kertas.
        
        Contoh:
        - Pilih tipe 'Kertas Isi' -> kodenya jadi 'KERTAS_ISI'
        - Pilih tipe 'Box' -> kodenya jadi 'BOX'
        
        Ini berguna buat:
        1. Gampang nyari produk
        2. Gampang filter di laporan
        3. Konsistensi penamaan
        """
        if self.tipe_kertas:
            # Set default_code sesuai tipe yang dipilih
            if self.tipe_kertas == 'isi':
                self.default_code = 'KERTAS_ISI'
            elif self.tipe_kertas == 'cover':
                self.default_code = 'KERTAS_COVER'
            elif self.tipe_kertas == 'plate_isi':
                self.default_code = 'PLATE_ISI'
            elif self.tipe_kertas == 'plate_cover':
                self.default_code = 'PLATE_COVER'
            elif self.tipe_kertas == 'box':
                self.default_code = 'BOX'


