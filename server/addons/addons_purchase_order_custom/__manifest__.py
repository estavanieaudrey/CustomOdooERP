{
    'name': 'Purchase Order Customization',
    'version': '1.0',
    'category': 'Purchases',
    'summary': 'Custom features for managing Purchase Orders',
    'depends': [
        'purchase',  # Core purchase module
        'purchase_requisition',  # For managing purchase agreements
        'addons_bom_custom',  # Custom BOM module
        'stock',  # For inventory management
        'mrp',  # For Bill of Materials (BOM)
        'sale',  # For sales integration
        'web',
    ],
    'data': [
        # XML files for views
        'views/purchase_agreement_views.xml',
        'views/purchase_order_custom_views.xml',
        'reports/report_rfq_template.xml',
        # Security and access control
        'security/ir.model.access.csv',
        'actions/request_for_quotation.xml',
    ],
    'installable': True,
    'application': False,
}
