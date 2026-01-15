import logging
import hmac
import hashlib
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class ChapaController(http.Controller):

    @http.route('/payment/chapa/redirect', type='http', auth='public', csrf=False)
    def chapa_redirect(self, item_id, **kwargs):
        """
        Entry point: User clicks 'Pay' -> This controller calls Chapa -> Redirects user to Chapa
        """
        tx = request.env['payment.transaction'].sudo().browse(int(item_id))
        if not tx or not tx.exists():
            return request.redirect('/shop/payment')

        try:
            checkout_url = tx._chapa_initiate_payment()
            return request.redirect(checkout_url)
        except Exception as e:
            _logger.exception("Chapa Redirect Failed")
            return request.redirect('/shop/payment?error=Chapa+Connection+Error')

    @http.route('/payment/chapa/return', type='http', auth='public', csrf=False)
    def chapa_return(self, **data):
        """
        User returns from Chapa. We verify the payment immediately.
        """
        _logger.info("Chapa Return: %s", data)
        try:
            request.env['payment.transaction'].sudo()._handle_notification_data('chapa', data)
        except Exception as e:
            _logger.exception("Chapa Return Verification Failed")
        
        return request.redirect('/payment/status')

    @http.route('/payment/chapa/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def chapa_webhook(self, **kwargs):
        """
        Chapa calls this URL asynchronously.
        We must verify the signature (x-chapa-signature) to ensure it's from Chapa.
        """
        raw_data = request.httprequest.data
        data = json.loads(raw_data)
        _logger.info("Chapa Webhook: %s", data)

        # 1. Identify the transaction to get the secret key
        tx_ref = data.get('tx_ref')
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', tx_ref)], limit=1)
        
        if not tx:
            _logger.warning("Chapa Webhook: Transaction not found for ref %s", tx_ref)
            return 'Transaction not found', 400

        # 2. Verify Signature
        # Chapa sends the HMAC-SHA256 signature of the payload in the 'x-chapa-signature' header
        signature = request.httprequest.headers.get('x-chapa-signature')
        webhook_secret = tx.provider_id.chapa_webhook_secret
        
        if webhook_secret and signature:
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                raw_data,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                _logger.warning("Chapa Webhook: Invalid Signature")
                return 'Invalid Signature', 403

        # 3. Process Payment
        try:
            request.env['payment.transaction'].sudo()._handle_notification_data('chapa', data)
        except Exception:
            _logger.exception("Chapa Webhook Processing Failed")
            return 'Error processing', 500

        return 'OK', 200
