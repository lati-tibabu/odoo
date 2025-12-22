# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Provider: Telebirr',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'Payment Provider: Telebirr Integration',
    'description': """
Telebirr Payment Provider
==========================

This module integrates Telebirr payment gateway with Odoo.

Telebirr is a mobile payment service in Ethiopia that allows users to make 
secure online payments. This module enables e-commerce websites built on Odoo 
to accept payments through Telebirr.

Features:
---------
* Support for online payment processing
* Webhook handling for payment notifications
* Transaction status tracking
* Refund support
* Test and production mode support

Configuration:
--------------
1. Go to Accounting/Payment Providers
2. Activate Telebirr
3. Enter your Telebirr API credentials (App ID, App Key, Public Key)
4. Configure the environment (Test/Production)
5. Save and publish the payment provider
    """,
    'depends': ['payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_telebirr_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_telebirr/static/src/js/payment_form.js',
        ],
    },
    'application': False,
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
