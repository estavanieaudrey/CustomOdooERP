from odoo import api, SUPERUSER_ID

# Function buat ngasih default code ke produk secara manual
# Ini dipake buat ngebedain jenis-jenis produk yang ada di sistem
def set_default_codes(cr, registry):
    # Bikin environment Odoo (kayak koneksi ke database gitu)
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Dictionary isinya nama produk dan kode defaultnya
    # Format: 'Nama Produk': 'KODE_DEFAULT'
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

    # Loop buat update setiap produk
    for product_name, default_code in products_to_update.items():
        # Cari produk berdasarkan nama (limit=1 artinya ambil yang pertama aja)
        product = env['product.product'].search([('name', '=', product_name)], limit=1)
        
        # Kalo ketemu produknya, update default code-nya
        if product:
            product.default_code = default_code
            print(f"Updated {product_name} with default_code: {default_code}")
        # Kalo ga ketemu, kasih tau lewat print
        else:
            print(f"Product {product_name} not found!")
