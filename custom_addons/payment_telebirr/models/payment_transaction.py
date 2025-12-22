# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import hashlib
import json
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_telebirr.controllers.main import TelebirrController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    telebirr_order_id = fields.Char(
        string='Telebirr Order ID',
        help='The order reference from Telebirr',
        readonly=True
    )

    def _get_specific_rendering_values(self, processing_values):
        """ Override to return Telebirr-specific rendering values.
        
        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'telebirr':
            return res

        # Prepare the payment request data
        base_url = self.provider_id.get_base_url()
        
        payload = {
            'merchant_id': self.provider_id.telebirr_merchant_id,
            'app_id': self.provider_id.telebirr_app_id,
            'nonce_str': payment_utils.generate_access_token(),
            'timestamp': fields.Datetime.now().strftime('%Y%m%d%H%M%S'),
            'out_trade_no': self.reference,
            'subject': f'Order {self.reference}',
            'total_amount': str(int(self.amount * 100)),  # Convert to cents
            'currency': self.currency_id.name,
            'notify_url': urls.url_join(base_url, TelebirrController._notify_url),
            'return_url': urls.url_join(base_url, TelebirrController._return_url),
            'timeout_express': '30m',
        }
        
        # Create signature
        sign_str = self._telebirr_generate_sign_string(payload)
        payload['sign'] = hashlib.sha256(
            (sign_str + self.provider_id.telebirr_app_key).encode()
        ).hexdigest()
        
        # Create the payment order
        try:
            api_url = self.provider_id._telebirr_get_api_url()
            response = self.provider_id._telebirr_make_request('/create_order', payload)
            
            if response.get('code') == 0 and response.get('data'):
                data = response['data']
                self.telebirr_order_id = data.get('order_id')
                
                rendering_values = {
                    'api_url': urls.url_join(api_url, '/h5pay'),
                    'prepay_id': data.get('prepay_id'),
                    'order_id': data.get('order_id'),
                }
                return rendering_values
            else:
                error_msg = response.get('msg', 'Unknown error')
                raise ValidationError(_("Telebirr: %s", error_msg))
                
        except Exception as e:
            _logger.exception("Error creating Telebirr payment order: %s", e)
            raise ValidationError(_("Could not create payment order. Please try again."))

    def _telebirr_generate_sign_string(self, params):
        """ Generate signature string for Telebirr API.
        
        :param dict params: The parameters to sign
        :return: The signature string
        :rtype: str
        """
        sorted_params = sorted(params.items())
        return '&'.join([f'{k}={v}' for k, v in sorted_params if v and k != 'sign'])

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override to find the transaction based on Telebirr data.
        
        :param str provider_code: The code of the provider handling the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'telebirr' or len(tx) == 1:
            return tx

        reference = notification_data.get('out_trade_no')
        if not reference:
            raise ValidationError(
                "Telebirr: " + _("Received data with missing reference (%s)", reference)
            )

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'telebirr')])
        if not tx:
            raise ValidationError(
                "Telebirr: " + _("No transaction found matching reference %s.", reference)
            )
        
        return tx

    def _process_notification_data(self, notification_data):
        """ Override to process the transaction based on Telebirr data.
        
        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'telebirr':
            return

        # Verify signature
        received_sign = notification_data.get('sign')
        params_to_sign = {k: v for k, v in notification_data.items() if k != 'sign'}
        sign_str = self._telebirr_generate_sign_string(params_to_sign)
        expected_sign = hashlib.sha256(
            (sign_str + self.provider_id.telebirr_app_key).encode()
        ).hexdigest()
        
        if received_sign != expected_sign:
            _logger.warning("Telebirr: Invalid signature for transaction %s", self.reference)
            raise ValidationError(_("Invalid signature received from Telebirr"))

        # Update transaction state based on payment status
        trade_status = notification_data.get('trade_status')
        self.telebirr_order_id = notification_data.get('order_id')
        
        if trade_status == 'TRADE_SUCCESS':
            self._set_done()
        elif trade_status == 'TRADE_CLOSED':
            self._set_canceled()
        elif trade_status == 'WAIT_BUYER_PAY':
            self._set_pending()
        else:
            _logger.warning(
                "Telebirr: Unknown trade status '%s' for transaction %s",
                trade_status, self.reference
            )
