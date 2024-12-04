from odoo import models, fields, api


class PurchaseOrderCustom(models.Model):
    _inherit = 'purchase.order'

    # Add fields for linking SO and MO
    sale_order_id = fields.Many2one('sale.order', string="Sales Order")
    manufacturing_order_id = fields.Many2one('mrp.production', string="Manufacturing Order")

    # Custom field for vendor address
    vendor_address = fields.Text(string="Vendor Address", compute="_compute_vendor_address")

    @api.depends('partner_id')
    def _compute_vendor_address(self):
        """Auto-fetch vendor address."""
        for record in self:
            record.vendor_address = record.partner_id.contact_address or "No Address Available"

    @api.onchange('manufacturing_order_id')
    def _onchange_manufacturing_order_id(self):
        """
        Auto-fill Products tab and fetch unit price from BoM.
        """
        if self.manufacturing_order_id:
            bom = self.manufacturing_order_id.bom_id
            if not bom:
                return

            # Clear existing lines
            self.order_line = [(5, 0, 0)]

            # Add new lines based on MO's raw materials
            new_lines = []
            for line in self.manufacturing_order_id.move_raw_ids:
                price_unit = self._get_price_from_bom(line.product_id, bom)
                new_lines.append((0, 0, {
                    'order_id': self.id,  # Explicitly set the order_id
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'price_unit': price_unit,
                    'name': line.product_id.display_name,
                }))

            self.order_line = new_lines

    def _get_price_from_bom(self, product_id, bom):
        """
        Fetch the price from BoM based on the product name and specific fields.
        """
        if not product_id or not bom:
            return 0.0

        # Mapping between product name keyword and BoM price fields
        price_field_mapping = {
            "Kertas Cover": "hrg_kertas_cover",
            "Kertas Isi": "hrg_kertas_isi",
            "Plate Cover": "hrg_plate_cover",
            "Plate Isi": "hrg_plate_isi",
            "Box": "hrg_box",
        }

        # Match the product name to the corresponding BoM field
        for keyword, field_name in price_field_mapping.items():
            if keyword in product_id.name:
                return getattr(bom, field_name, 0.0)

        return 0.0  # Default to 0 if no match


class PurchaseOrderLineCustom(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'order_id.manufacturing_order_id')
    def _onchange_product_id(self):
        """
        Set price_unit based on BoM whenever product_id or manufacturing_order_id changes.
        """
        if self.product_id and self.order_id.manufacturing_order_id:
            bom = self.order_id.manufacturing_order_id.bom_id
            self.price_unit = self.order_id._get_price_from_bom(self.product_id, bom)


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Override vendor price influence. Prevent price_unit from being updated by partner.
        """
        pass  # Do nothing to ensure price_unit is not affected by vendor pricelist.

    @api.model
    def create(self, vals):
        """
        Set price_unit from BoM during record creation to override default vendor price logic.
        """
        record = super(PurchaseOrderLineCustom, self).create(vals)
        if record.product_id and record.order_id.manufacturing_order_id:
            bom = record.order_id.manufacturing_order_id.bom_id
            record.price_unit = record.order_id._get_price_from_bom(record.product_id, bom)
        return record

    def write(self, vals):
        """
        Set price_unit from BoM during record update to override default vendor price logic.
        """
        res = super(PurchaseOrderLineCustom, self).write(vals)
        for line in self:
            if 'product_id' in vals or 'order_id' in vals:
                if line.product_id and line.order_id.manufacturing_order_id:
                    bom = line.order_id.manufacturing_order_id.bom_id
                    line.price_unit = line.order_id._get_price_from_bom(line.product_id, bom)
        return res

