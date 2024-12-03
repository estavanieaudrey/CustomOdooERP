{
    'name': 'Manufacturing Order Customization',
    'version': '1.0',
    'summary': 'Customization for Manufacturing Orders (MO) / SPK in Odoo',
    'description': """
        Custom module to enhance Manufacturing Orders (MO) with additional fields, 
        SPK details, and integration with Sales Orders and Bill of Materials (BoM).
    """,
    'author': 'Your Name',
    'depends': ['mrp', 'sale', 'product', 'base'],
    'data': [
        'views/manufacturing_order_view.xml',
        'views/nota_permintaan_barang_view.xml',
        'reports/report_npb_template.xml',
    ],
    'installable': True,
    'application': False,
}
