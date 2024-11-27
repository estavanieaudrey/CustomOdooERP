from odoo import api, SUPERUSER_ID

# Menambahkan Default Code Secara Manual
# ini digunakan untuk identify jenis produk yang ada
def set_default_codes(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Daftar produk yang harus diperbarui
    products_to_update = {
        'Kertas Isi (Virgin/HS)': 'KERTAS_ISI',
        'Kertas Isi (Tabloid)': 'KERTAS_ISI',
        'Kertas Cover (Art Carton)': 'KERTAS_COVER',
        'Kertas Cover (Art Paper)': 'KERTAS_COVER',
        'Kertas Cover (Ivory)': 'KERTAS_COVER',
        'Kertas Cover (Boxboard)': 'KERTAS_COVER',
        'Kertas Cover (Duplex)': 'KERTAS_COVER',
        'Box Buku': 'BOX',
    }

    for product_name, default_code in products_to_update.items():
        product = env['product.product'].search([('name', '=', product_name)], limit=1)
        if product:
            product.default_code = default_code
            print(f"Updated {product_name} with default_code: {default_code}")
        else:
            print(f"Product {product_name} not found!")
