{
    'name': 'Inventory Customization',
    'version': '1.0',
    'summary': 'Custom fields and functionalities for Inventory module',
    'description': """
        This module adds custom fields and functionalities to the Inventory module,
        including Resi Number, Container Number, and Container Arrival Date.
    """,
    'author': 'Your Name',
    'depends': [
        'base',
        'stock',
        'mrp',  # jika menggunakan manufacturing
        'sale',
    ],
    'data': [
        'views/inventory_custom_views.xml',
        'reports/inventory_custom_template.xml',
        'reports/inventory_deliveryslip_template.xml',
        'actions/inventory_custom_action.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
