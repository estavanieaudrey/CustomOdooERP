from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agreement_title = fields.Char(string="Judul Perjanjian")
    customer_signature = fields.Binary(string="Tanda Tangan Customer")
    validity_date = fields.Date(string="Tanggal Kedaluwarsa")
    is_signed = fields.Boolean(string="Apakah Ditandatangani?", default=False)

    def action_convert_to_order(self):
        for order in self:
            if not order.is_signed:
                raise UserError("Dokumen belum ditandatangani oleh customer.")
            order.action_confirm()
