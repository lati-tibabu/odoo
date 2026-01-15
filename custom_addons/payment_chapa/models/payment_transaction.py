import logging
import requests
import hmac
import hashlib
import re
from werkzeug import urls

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """
        Override to return the data needed for the redirect.
        We return the URL to our own controller which will handle the API call.
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'chapa':
            return res

        # Check for dummy key
        if self.provider_id.chapa_secret_key == 'dummy':
            raise ValidationError("Please configure your Chapa Secret Key in Payment Providers.")

        base_url = self.provider_id.get_base_url()
        webhook_url = urls.url_join(base_url, '/payment/chapa/webhook')
        # We pass the original reference in the return URL queries
        return_url = urls.url_join(base_url, f'/payment/chapa/return?ref={self.reference}')
        
        first_name, last_name = payment_utils.split_partner_name(self.partner_name)

        # Sanitize data for Chapa
        # tx_ref must be alphanumeric + hyphens/dots/underscores.
        # We include ID to be able to find it back reliably if the reference is mangled.
        sanitized_ref = re.sub(r'[^a-zA-Z0-9.\-_]', '-', self.reference)
        chapa_tx_ref = f"{self.id}-{sanitized_ref}"

        # Customization Title: Max 16, alphanumeric + chars
        company_name = self.company_id.name or "Odoo"
        sanitized_title = re.sub(r'[^a-zA-Z0-9.\-_ ]', '', company_name)[:16]

        # Customization Description: alphanumeric + chars
        sanitized_desc = re.sub(r'[^a-zA-Z0-9.\-_ ]', '-', self.reference)

        payload = {
            "amount": str(self.amount),
            "currency": self.currency_id.name,
            "email": self.partner_email or self.partner_id.email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": chapa_tx_ref,
            "callback_url": webhook_url,
            "return_url": return_url,
            "customization": {
                "title": sanitized_title,
                "description": sanitized_desc
            }
        }
        
        headers = {
            'Authorization': f'Bearer {self.provider_id.chapa_secret_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post('https://api.chapa.co/v1/transaction/initialize', json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success' and data.get('data', {}).get('checkout_url'):
                checkout_url = data['data']['checkout_url']
                return {'api_url': checkout_url}
            else:
                _logger.error("Chapa Init Error: %s", data)
                raise ValidationError(data.get('message', 'Chapa initialization failed.'))

        except requests.exceptions.HTTPError as e:
            msg = "Chapa Error: %s" % e
            try:
                error_data = e.response.json()
                msg = error_data.get('message', msg)
                _logger.error("Chapa API Error: %s", error_data)
            except Exception:
                pass
            raise ValidationError(msg)
        except ValidationError:
            raise
        except Exception as e:
            _logger.exception("Failed to initialize Chapa transaction")
            raise ValidationError("Could not communicate with Chapa.")

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Find the transaction based on the reference (tx_ref) returned by Chapa.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'chapa' or len(tx) == 1:
            return tx

        # Chapa sends 'tx_ref' in webhook and 'ref' (custom param) in return URL
        reference = notification_data.get('tx_ref') or notification_data.get('ref')
        if not reference:
            raise ValidationError("Chapa: No reference found in notification data.")

        # 1. Try finding by exact reference (if it came from return_url 'ref' param)
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'chapa')])
        if tx:
            return tx
        
        # 2. Try finding by ID from chapa_tx_ref (if it came from webhook 'tx_ref')
        # Structure: "{id}-{sanitized_ref}"
        try:
            tx_id_str = reference.split('-')[0]
            if tx_id_str.isdigit():
                tx = self.browse(int(tx_id_str))
                if tx.exists() and tx.provider_code == 'chapa':
                    # Optional: Verify the rest matches loosely if needed
                    return tx
        except Exception:
            pass

        raise ValidationError(f"Chapa: No transaction found for reference {reference}.")
        
    def _process_notification_data(self, notification_data):
        """
        Verify the transaction status with Chapa using the Verify API.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'chapa':
            return
            
        # Note: If we found tx by ID ref, the 'notification_data' might have the chapa ref
        # but the verify URL needs the tx_ref sent to Chapa.
        chapa_tx_ref = notification_data.get('tx_ref')
        
        # If we are verifying from Return URL, we might only have 'ref' (Odoo Ref).
        # But we need the 'tx_ref' (Chapa Ref) to call the Verify API.
        # Chapa's Verify API endpoint is /transaction/verify/{tx_ref}
        # If we don't have the chapa_tx_ref from the payload, we must reconstruct it OR
        # rely on what we sent.
        # BUT: reconstructing sanitized ref is risky if logic changed.
        # LUCKILY: The Return URL does usually NOT contain the tx_ref unless we asked for it?
        # Chapa docs say: "When the payment is successful, we will redirect the user to your return_url."
        # It doesn't explicitly say it appends the tx_ref.
        # However, usually we can also verify by the reference we generated.
        
        # Recommendation: If we only have Odoo reference, we should reconstruct the chapa ref 
        # to verify.
        if not chapa_tx_ref:
            # Reconstruct logic must match _get_specific_rendering_values
            sanitized_ref = re.sub(r'[^a-zA-Z0-9.\-_]', '-', self.reference)
            chapa_tx_ref = f"{self.id}-{sanitized_ref}"

        # Prepare Verification
        headers = {'Authorization': f'Bearer {self.provider_id.chapa_secret_key}'}
        verify_url = f"https://api.chapa.co/v1/transaction/verify/{chapa_tx_ref}"

        try:
            response = requests.get(verify_url, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            # Check status inside data -> data -> status
            payment_data = data.get('data', {})
            status = payment_data.get('status')
            
            if status == 'success':
                self._set_done()
            elif status == 'failed':
                self._set_canceled()
            else:
                _logger.warning("Chapa: Transaction %s is in state %s", self.reference, status)
                # Leave in draft or set pending
                
        except Exception as e:
            _logger.exception("Chapa Verification Failed")
            raise ValidationError("Chapa verification failed. Please try again later.")
