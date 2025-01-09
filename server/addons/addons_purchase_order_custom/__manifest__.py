{
    'name': 'Purchase Order Customization',
    'version': '1.0',
    'category': 'Purchases',
    'summary': 'Custom features for managing Purchase Orders',
    'depends': ['purchase', 'stock', 'mrp', 'sale'],
    'data': [
        'views/purchase_order_custom_views.xml',
        'views/stock_picking_custom.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
