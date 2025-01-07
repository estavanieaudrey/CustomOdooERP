from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    resi_number = fields.Char(string="Nomor Resi")
    container_number = fields.Char(string="Nomor Kontainer")
    container_arrival_date = fields.Date(string="Tanggal Kedatangan Kontainer")
