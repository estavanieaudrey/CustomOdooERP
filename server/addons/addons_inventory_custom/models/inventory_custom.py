from odoo import models, fields

# Class untuk nambahin fitur custom di stock.picking (transfer barang)
class StockPicking(models.Model):
    _inherit = 'stock.picking'  # Inherit dari stock.picking bawaan Odoo

    # Field buat nyimpen nomor resi pengiriman
    resi_number = fields.Char(
        string="Nomor Resi",
        help="Nomor resi dari ekspedisi/kurir"
    )

    # Field buat nyimpen nomor kontainer (kalo pake kontainer)
    container_number = fields.Char(
        string="Nomor Kontainer",
        help="Nomor kontainer untuk pengiriman"
    )

    # Field buat nyimpen tanggal kedatangan kontainer
    container_arrival_date = fields.Date(
        string="Tanggal Kedatangan Kontainer",
        help="Perkiraan tanggal kontainer sampai"
    )