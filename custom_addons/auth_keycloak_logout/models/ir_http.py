import logging
import time
import requests
from odoo import models, http, api, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        # 1. Standard authentication first
        res = super(IrHttp, cls)._authenticate(endpoint)

        # 2. Keycloak session check (Lazy sync)
        # Only check for endpoints that strictly require a user session to avoid loops on login page
        auth = endpoint.routing.get('auth')
        if auth == 'user' and request.session.uid and request.session.get('keycloak_sid'):
            cls._check_keycloak_session()

        return res

    @classmethod
    def _check_keycloak_session(cls):
        """
        Check if the Keycloak session is still valid.
        We do this periodically to avoid hammering Keycloak on every request.
        """
        now = time.time()
        last_check = request.session.get('last_kc_check', 0)
        
        # Check every 5 seconds (can be adjusted)
        if now - last_check < 5:
            return

        request.session['last_kc_check'] = now
        
        uid = request.session.uid
        # We need the user record and the provider info
        user = request.env['res.users'].sudo().browse(uid)
        refresh_token = request.session.get('refresh_token') or user.oauth_refresh_token
        provider = user.oauth_provider_id
        
        if not (refresh_token and provider and provider.enabled):
            return

        _logger.debug("Checking Keycloak session status for user %s", user.login)
        
        try:
            # We try to "introspect" or perform a "token refresh" (no-op) 
            # to see if Keycloak still likes us.
            token_endpoint = provider.token_endpoint or provider.validation_endpoint
            
            payload = {
                'client_id': provider.client_id,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            }
            if provider.client_secret:
                payload['client_secret'] = provider.client_secret
            
            # Note: We use a short timeout to not block the user request too long
            response = requests.post(token_endpoint, data=payload, timeout=3)
            
            if response.status_code != 200:
                # Keycloak rejected the refresh token, session is likely dead
                _logger.info("Keycloak session for user %s is no longer valid (Status %s). Logging out.", 
                             user.login, response.status_code)
                request.session.logout(keep_db=True)
                # Force save to ensure logout persists despite the exception redirect
                from odoo.http import root
                root.session_store.save(request.session)
                raise http.SessionExpiredException("Keycloak session expired")
            
            # Update the session tokens if they rotated
            data = response.json()
            if data.get('refresh_token'):
                new_refresh = data['refresh_token']
                request.session['refresh_token'] = new_refresh
                # Also update user record for persistence across browser sessions if needed
                user.write({'oauth_refresh_token': new_refresh})
            if data.get('id_token'):
                 request.session['id_token'] = data['id_token']
                 user.write({'oauth_id_token': data['id_token']})
            
            # Force save session to persist last_kc_check and new tokens
            from odoo.http import root
            root.session_store.save(request.session)

        except requests.exceptions.RequestException as e:
            _logger.warning("Failed to contact Keycloak for session check: %s", e)
        except http.SessionExpiredException:
            raise
        except Exception as e:
            _logger.error("Unexpected error during Keycloak session check: %s", e)
