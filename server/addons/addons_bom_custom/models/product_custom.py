from odoo import models, fields, api

from python.Lib.email.policy import default


class ProductCustom(models.Model):
    _inherit = "product.template"

    # Fields untuk product tipe kertas
    tipe_kertas = fields.Selection([
        ('isi', 'Kertas Isi'),
        ('cover', 'Kertas Cover')
    ], string="Tipe Kertas", default="isi")

    @api.onchange('tipe_kertas')
    def _onchange_tipe_kertas(self):
        """Update default_code when tipe_kertas changes"""
        if self.tipe_kertas:
            if self.tipe_kertas == 'isi':
                self.default_code = 'KERTAS_ISI'
            elif self.tipe_kertas == 'cover':
                self.default_code = 'KERTAS_COVER'


