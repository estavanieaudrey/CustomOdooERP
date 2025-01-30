{
    'name': 'Manufacturing Order Customization',
    'version': '1.0',
    'summary': 'Customization for Manufacturing Orders (MO) / SPK in Odoo',
    'description': """
        Custom module to enhance Manufacturing Orders (MO) with additional fields, 
        SPK details, and integration with Sales Orders and Bill of Materials (BoM).
    """,
    'author': 'Your Name',
    'depends': ['mrp', 'sale', 'product', 'base', 'sale_stock', 'addons_inventory_custom'],
    'data': [
        'views/manufacturing_order_view.xml',
        'views/nota_permintaan_barang_view.xml',
        'views/surat_perintah_kerja.xml',
        'reports/report_npb_template.xml',
        'reports/report_spk_template.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
