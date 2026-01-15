{
    'name': 'Chapa Payment Provider',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'A generic payment provider for Chapa (Ethiopia)',
    'depends': ['payment'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_chapa_templates.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'application': False,
    'license': 'LGPL-3',
}
