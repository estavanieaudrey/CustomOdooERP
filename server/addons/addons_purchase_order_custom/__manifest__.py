{
    'name': 'Purchase Order Customization',
    'version': '1.0',
    'category': 'Purchases',
    'summary': 'Custom features for managing Purchase Orders',
    'depends': ['purchase', 'mrp', 'sale'],
    'data': [
        'views/purchase_order_custom_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
