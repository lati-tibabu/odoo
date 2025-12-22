# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import hashlib
import json
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('telebirr', 'Telebirr')],
        ondelete={'telebirr': 'set default'}
    )
    telebirr_app_id = fields.Char(
        string='App ID',
        help='The App ID provided by Telebirr',
        required_if_provider='telebirr',
        groups='base.group_system'
    )
    telebirr_app_key = fields.Char(
        string='App Key',
        help='The App Key provided by Telebirr',
        required_if_provider='telebirr',
        groups='base.group_system'
    )
    telebirr_public_key = fields.Text(
        string='Public Key',
        help='The RSA Public Key provided by Telebirr',
        required_if_provider='telebirr',
        groups='base.group_system'
    )
    telebirr_merchant_id = fields.Char(
        string='Merchant ID',
        help='The Merchant ID provided by Telebirr',
        required_if_provider='telebirr',
        groups='base.group_system'
    )

    @api.model
    def _get_compatible_providers(self, *args, company_id=None, **kwargs):
        """ Override to filter out Telebirr providers for unsupported currencies. """
        providers = super()._get_compatible_providers(*args, company_id=company_id, **kwargs)
        
        # Telebirr primarily supports Ethiopian Birr (ETB)
        currency = kwargs.get('currency_id')
        if currency:
            currency = self.env['res.currency'].browse(currency)
            providers = providers.filtered(
                lambda p: p.code != 'telebirr' or currency.name == 'ETB'
            )
        
        return providers

    def _telebirr_get_api_url(self):
        """ Return the API URL according to the provider state.
        
        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        
        if self.state == 'enabled':
            # Production URL
            return 'https://api.telebirr.com/gateway'
        else:
            # Test/Sandbox URL
            return 'https://test-api.telebirr.com/gateway'

    def _get_default_payment_method_codes(self):
        """ Override to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'telebirr':
            return default_codes
        return ['card']

    def _telebirr_make_request(self, endpoint, payload=None):
        """ Make a request to Telebirr API.
        
        :param str endpoint: The endpoint to be reached by the request
        :param dict payload: The payload of the request
        :return: The JSON-formatted content of the response
        :rtype: dict
        """
        self.ensure_one()
        
        url = urls.url_join(self._telebirr_get_api_url(), endpoint)
        
        headers = {
            'Content-Type': 'application/json',
            'X-APP-ID': self.telebirr_app_id,
        }
        
        # Add signature to the request
        if payload:
            payload_str = json.dumps(payload, sort_keys=True)
            sign_str = payload_str + self.telebirr_app_key
            signature = hashlib.sha256(sign_str.encode()).hexdigest()
            headers['X-SIGNATURE'] = signature
        
        try:
            response = self.env['ir.http']._request(
                url, json=payload, headers=headers, method='POST'
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            _logger.exception("Telebirr API request failed: %s", e)
            raise ValidationError(_("Could not connect to Telebirr. Please try again later."))
