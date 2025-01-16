{
    'name': 'Bill Of Material Customization',
    'version': '1.0.0',
    'summary': 'Customize BOM to include cost and price calculation',
    'description': 'Add custom fields and logic to BOM (Bill of Materials).',
    'author': 'Custom BOM Odre',
    'depends': ['base', 'mrp', 'product', 'purchase_requisition'],
    'post_init_hook': 'set_default_codes',  # Hubungkan fungsi saat modul di-upgrade
    'data': [
        'views/bom_custom_views.xml',
        'views/product_custom_views.xml',

    ],
    'installable': True,
    'application': False,
}
