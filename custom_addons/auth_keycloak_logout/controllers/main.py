from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.session import Session
from urllib.parse import urlencode


import logging
import requests
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.session import Session
from urllib.parse import urlencode

_logger = logging.getLogger(__name__)

class KeycloakSession(Session):

    @http.route("/web/session/logout", type="http", auth="none", csrf=False)
    def logout(self, redirect="/web/login", **kwargs):
        # 0. Get tokens and provider info before destroying session
        uid = request.session.uid
        id_token = request.session.get('id_token')
        refresh_token = request.session.get('refresh_token')
        
        # If not in session, try to get from user record if we have a UID
        if uid:
            user = request.env['res.users'].sudo().browse(uid)
            if not id_token:
                id_token = user.oauth_id_token
            if not refresh_token:
                refresh_token = user.oauth_refresh_token
            provider = user.oauth_provider_id
        else:
            provider = request.env["auth.oauth.provider"].sudo().search(
                [("enabled", "=", True), ("auth_endpoint", "ilike", "keycloak")],
                limit=1,
            )

        # 1. Destroy Odoo session
        request.session.logout(keep_db=True)

        if not provider:
            _logger.debug("No OAuth provider found for logout redirect")
            return request.redirect(redirect)

        # 2. Backchannel Logout (Optional but good for full implementation)
        # If we have a refresh token, we can tell Keycloak to invalidate it immediately
        if refresh_token:
            try:
                logout_endpoint = provider.validation_endpoint.replace(
                    "/protocol/openid-connect/token",
                    "/protocol/openid-connect/logout"
                )
                # If auth_oidc has end_session_endpoint, it might be better
                if hasattr(provider, 'end_session_endpoint') and provider.end_session_endpoint:
                    # Note: end_session_endpoint is usually for browser redirect
                    pass
                
                token_endpoint = getattr(provider, 'token_endpoint', False) or provider.validation_endpoint
                # Backchannel logout endpoint is often the same as browser logout but called via POST
                # or specifically a /logout endpoint.
                bc_logout_url = token_endpoint.replace('/token', '/logout')
                
                payload = {
                    'client_id': provider.client_id,
                    'refresh_token': refresh_token,
                }
                if provider.client_secret:
                    payload['client_secret'] = provider.client_secret
                
                requests.post(bc_logout_url, data=payload, timeout=5)
                _logger.info("Backchannel logout successful for user %s", uid)
            except Exception as e:
                _logger.warning("Backchannel logout failed: %s", e)

        # 3. RP-Initiated Logout (Browser Redirect)
        # This is the most important part for web sessions
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url") or request.httprequest.host_url.rstrip('/')
        
        if redirect.startswith('/'):
            redirect_uri = f"{base_url}{redirect}"
        else:
            redirect_uri = redirect
            
        # Add no_redirect to avoid login loops with auto-redirect modules
        if '?' in redirect_uri:
            redirect_uri += '&no_redirect=1'
        else:
            redirect_uri += '?no_redirect=1'

        params = {
            "client_id": provider.client_id,
            "post_logout_redirect_uri": redirect_uri,
        }
        
        if id_token:
            params["id_token_hint"] = id_token

        # # Determine logout URL
        # logout_url = getattr(provider, 'end_session_endpoint', False)
        # if not logout_url:
        #     # Fallback to derivation or hardcoded if necessary
        #     # We use the one provided by the user earlier as primary fallback for their specific setup
        #     logout_url = "http://localhost:8080/realms/odoo-realm/protocol/openid-connect/logout"

        # final_url = f"{logout_url}?{urlencode(params)}"
        # _logger.debug("Redirecting to Keycloak logout: %s", final_url)
        return request.redirect(base_url)
