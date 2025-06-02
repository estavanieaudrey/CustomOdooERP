from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _hide_my_dashboard(self):
        """Method untuk menyembunyikan menu My Dashboard"""
        try:
            # Coba gunakan external ID
            menu = self.env.ref('spreadsheet_dashboard.spreadsheet_dashboard_menu_my', False)
            if menu:
                menu.active = False
                return True

            # Fallback jika external ID tidak ditemukan
            my_dashboard = self.search([('name', '=', 'My Dashboard')], limit=1)
            if my_dashboard:
                my_dashboard.active = False
                return True

            return False
        except Exception as e:
            self.env.cr.rollback()
            return False