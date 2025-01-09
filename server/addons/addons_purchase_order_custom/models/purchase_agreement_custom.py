from odoo import models, fields, api
from datetime import date

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    material_category = fields.Selection(
        [
            ('KERTAS_ISI', 'Kertas Isi'),
            ('KERTAS_COVER', 'Kertas Cover'),
            ('PLATE_ISI', 'Plate Isi'),
            ('PLATE_COVER', 'Plate Cover'),
            ('BOX', 'Box'),
            ('UV', 'UV'),
        ],
        string="Material Category",
        compute="_compute_material_category",
        store=True,
        help="Category derived from product for easier grouping."
    )
    is_valid = fields.Boolean(
        string="Is Valid",
        compute="_compute_is_valid",
        store=True,
        help="Indicates whether the requisition is valid for the current date."
    )

    @api.depends('line_ids.product_id')
    def _compute_material_category(self):
        """Automatically derive the material category based on product_id."""
        material_map = {
            'Kertas Isi (Virgin/HS)': 'KERTAS_ISI',
            'Kertas Isi (Tabloid)': 'KERTAS_ISI',
            'Kertas Cover (Art Carton)': 'KERTAS_COVER',
            'Kertas Cover (Art Paper)': 'KERTAS_COVER',
            'Kertas Cover (Ivory)': 'KERTAS_COVER',
            'Kertas Cover (Boxboard)': 'KERTAS_COVER',
            'Kertas Cover (Duplex)': 'KERTAS_COVER',
            'Plate Isi': 'PLATE_ISI',
            'Plate Cover': 'PLATE_COVER',
            'Box Buku': 'BOX',
            'UV': 'UV',
        }
        for requisition in self:
            product = requisition.line_ids.mapped('product_id.name')
            requisition.material_category = material_map.get(product[0], False) if product else False


    @api.depends('date_start', 'date_end')
    def _compute_is_valid(self):
        """Check if the requisition falls within its validity period."""
        today = date.today()
        for requisition in self:
            requisition.is_valid = (
                requisition.date_start <= today <= requisition.date_end
                if requisition.date_start and requisition.date_end else False
            )

    # Ensure proper ordering to avoid ORM errors
    _order = "create_date desc"
