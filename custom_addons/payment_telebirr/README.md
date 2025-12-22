# Payment Provider: Telebirr

## Overview

This module provides integration between Odoo and Telebirr, enabling Ethiopian businesses to accept mobile payments through the Telebirr payment gateway.

## Features

- **Secure Payment Processing**: All transactions are processed securely through Telebirr's payment gateway
- **Mobile Payment Support**: Accept payments from Telebirr mobile wallet users
- **Real-time Payment Notifications**: Receive instant notifications for payment status updates
- **Test & Production Environments**: Support for both sandbox testing and live production environments
- **Transaction Management**: Full transaction lifecycle management including refunds
- **Ethiopian Birr (ETB) Support**: Primary support for ETB currency
- **Webhook Integration**: Automated payment status updates via webhook callbacks

## Installation

1. Install the module through the Odoo Apps menu
2. Or place the `payment_telebirr` folder in your Odoo addons directory
3. Update the app list in Odoo
4. Install the "Payment Provider: Telebirr" module

## Configuration

### Prerequisites

Before configuring the module, you need to:
1. Register for a Telebirr merchant account
2. Obtain your API credentials from Telebirr:
   - App ID
   - App Key
   - Merchant ID
   - RSA Public Key

### Setup Steps

1. Go to **Accounting → Configuration → Payment Providers**
2. Find and open **Telebirr**
3. Configure the following settings:

   **Basic Settings:**
   - **State**: Choose "Test" for sandbox or "Enabled" for production
   - **Display As**: How the payment option appears to customers

   **Credentials:**
   - **App ID**: Your Telebirr App ID
   - **App Key**: Your Telebirr App Key
   - **Merchant ID**: Your Telebirr Merchant ID
   - **Public Key**: Your RSA Public Key from Telebirr

4. Click **Save**
5. Click **Publish** to make the payment provider available to customers

## Usage

Once configured, Telebirr will appear as a payment option during checkout for customers in Ethiopia.

### Payment Flow

1. Customer selects Telebirr as payment method
2. Customer is redirected to Telebirr payment page
3. Customer completes payment using their Telebirr mobile wallet
4. Customer is redirected back to your store
5. Payment status is updated automatically via webhook

## Testing

For testing purposes:
1. Set the payment provider state to "Test"
2. Use Telebirr's test environment credentials
3. Perform test transactions using Telebirr's test mobile numbers

## Security

- All API communications are encrypted
- Webhook notifications are verified using HMAC signatures
- Sensitive credentials are stored securely and never exposed to end users
- Support for Odoo's standard security groups and access controls

## Support

For issues related to:
- **Module functionality**: Create an issue in the repository
- **Telebirr API**: Contact Telebirr support
- **Odoo integration**: Consult Odoo documentation

## Technical Details

### Models

- **payment.provider**: Extended to support Telebirr configuration
- **payment.transaction**: Extended to handle Telebirr transactions

### Controllers

- **/payment/telebirr/return**: Handles return from Telebirr payment page
- **/payment/telebirr/notify**: Webhook endpoint for payment notifications

### API Integration

The module integrates with Telebirr's REST API:
- Production: `https://api.telebirr.com/gateway`
- Sandbox: `https://test-api.telebirr.com/gateway`

## Requirements

- Odoo 14.0 or higher
- payment module (core Odoo)
- Active Telebirr merchant account

## License

LGPL-3

## Authors

- Developed for Odoo integration with Telebirr payment gateway

## Version History

- **1.0**: Initial release
  - Basic payment processing
  - Webhook support
  - Test and production mode
  - ETB currency support
