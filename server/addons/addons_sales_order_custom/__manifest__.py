{
    'name': 'Sales Order Customization',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Sales',
    'depends': ['sale', 'mrp', 'web', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'report/draft_perjanjian_template.xml',
        'views/draft_perjanjian_view.xml',
    ],
    'installable': True,
    'application': False,
}
