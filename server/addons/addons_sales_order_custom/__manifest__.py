{
    'name': 'Custom Sales Order',
    'version': '1.0',
    'author': 'Custom SO Odre',
    'category': 'Sales',
    'depends': ['sale'],  # Modul yang diwarisi
    'data': [
        'views/sale_order_view.xml',
        'report/sale_order_report.xml',  # krn ada laporan
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
