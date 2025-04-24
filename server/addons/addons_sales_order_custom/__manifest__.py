{
    'name': 'Sales Order Customization',
    'version': '1.0',
    'author': 'Your Name',
    'category': 'Sales',
    'depends': ['sale', 'sale_management', 'mrp', 'web', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'report/draft_perjanjian_template.xml',
        'report/all_invoices.xml',
        'actions/draft_perjanjian_action.xml',
        'actions/all_invoices_action.xml',
    ],
    'installable': True,
    'application': False,
}
