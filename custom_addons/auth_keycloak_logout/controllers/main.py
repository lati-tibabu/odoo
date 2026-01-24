import logging
import requests
import json
import base64
from odoo import http, SUPERUSER_ID
from odoo.http import request, root
from odoo.addons.web.controllers.session import Session
from odoo.addons.keycloack_auth.controllers.sso import KeycloakSSO
from urllib.parse import urlencode

_logger = logging.getLogger(__name__)

try:
    from jose import jwt
except ImportError:
    jwt = None

class KeycloakSSOExtended(KeycloakSSO):
    @http.route(['/auth/sso/callback', '/sso/jwt/login'], type='http', auth='none', methods=['POST'], csrf=False)
    def sso_callback(self, **post):
        response = super(KeycloakSSOExtended, self).sso_callback(**post)
        
        # If login was successful, capture tokens from original post
        token = post.get('access_token')
        refresh_token = post.get('refresh_token')
        
        if request.session.uid:
            if refresh_token:
                request.session['refresh_token'] = refresh_token
                
            if token:
                try:
                    parts = token.split('.')
                    if len(parts) > 1:
                        payload_b64 = parts[1]
                        payload_b64 += '=' * (4 - len(payload_b64) % 4)
                        payload = json.loads(base64.b64decode(payload_b64))
                        sid = payload.get('sid')
                        if sid:
                            request.session['keycloak_sid'] = sid
                            # Force save to ensure it's written to disk before the redirect
                            root.session_store.save(request.session)
                            _logger.info("SSO Callback: Captured Keycloak sid %s for user %s", sid, request.session.uid)
                except Exception as e:
                    _logger.warning("SSO Callback: Failed to extract sid from token: %s", e)
        
        return response

class KeycloakSession(Session):

    @http.route("/web/session/logout", type="http", auth="none", csrf=False)
    def logout(self, redirect="/web/login", **kwargs):
        # 0. Get tokens and provider info before destroying session
        uid = request.session.uid
        id_token = request.session.get('id_token')
        refresh_token = request.session.get('refresh_token')
        
        provider = False
        if uid:
            user = request.env['res.users'].sudo().browse(uid)
            if not id_token:
                id_token = user.oauth_id_token
            if not refresh_token:
                refresh_token = user.oauth_refresh_token
            provider = user.oauth_provider_id
        
        if not provider:
            provider = request.env["auth.oauth.provider"].sudo().search(
                [("enabled", "=", True), ("auth_endpoint", "ilike", "keycloak")],
                limit=1,
            )

        # 1. Destroy Odoo session
        request.session.logout(keep_db=True)

        if not provider:
            _logger.debug("No OAuth provider found for logout redirect")
            return request.redirect(redirect)

        # 2. Backchannel Logout (Telling Keycloak to invalidate refresh token)
        if refresh_token:
            try:
                token_endpoint = provider.token_endpoint or provider.validation_endpoint
                bc_logout_url = token_endpoint.replace('/token', '/logout')
                
                payload = {
                    'client_id': provider.client_id,
                    'refresh_token': refresh_token,
                }
                if provider.client_secret:
                    payload['client_secret'] = provider.client_secret
                
                requests.post(bc_logout_url, data=payload, timeout=5)
                _logger.info("Backchannel logout (revocation) successful for user %s", uid)
            except Exception as e:
                _logger.warning("Backchannel logout (revocation) failed: %s", e)

        # 3. RP-Initiated Logout (Browser Redirect)
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url") or request.httprequest.host_url.rstrip('/')
        
        if redirect.startswith('/'):
            redirect_uri = f"{base_url}{redirect}"
        else:
            redirect_uri = redirect
            
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

        # Use end_session_endpoint if available from auth_oidc
        logout_url = getattr(provider, 'end_session_endpoint', False)
        if not logout_url:
            # Prefer token/validation endpoints (more reliable than auth_endpoint)
            endpoint = provider.token_endpoint or provider.validation_endpoint or provider.auth_endpoint
            if endpoint and endpoint.endswith('/token'):
                logout_url = endpoint[:-len('/token')] + '/logout'
            elif endpoint:
                # Fallback derivation
                logout_url = endpoint.replace('/auth', '/logout')

        final_url = f"{logout_url}?{urlencode(params)}"
        _logger.debug("Redirecting to Keycloak logout: %s", final_url)
        # return request.redirect(final_url)
        return request.redirect(base_url) # Just redirect to Odoo login page to avoid logout loops since module (auth_keycloak_login_redirect) handles backchannel logout

    @http.route('/auth/keycloak/backchannel_logout', type='http', auth='none', methods=['POST'], csrf=False)
    def backchannel_logout(self, **post):
        """
        Handle OIDC Back-channel Logout from Keycloak.
        """
        _logger.info("Received Keycloak Back-channel Logout request")
        logout_token = post.get('logout_token')
        if not logout_token:
            _logger.warning("Back-channel logout: Missing logout_token in POST data: %s", post)
            return request.make_response('Missing logout_token', status=400)

        sudo_env = request.env(user=SUPERUSER_ID)
        
        try:
            # Extract unverified payload to find sid/sub
            parts = logout_token.split('.')
            if len(parts) < 2:
                _logger.warning("Back-channel logout: Invalid JWT format")
                return request.make_response("Invalid JWT", status=400)
                
            payload_b64 = parts[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(payload_b64))
            
            sid = payload.get('sid')
            sub = payload.get('sub')
            
            _logger.info("Back-channel logout processing for sid: %s, sub: %s", sid, sub)

            if not sid and not sub:
                _logger.warning("Back-channel logout: Token missing sid and sub")
                return request.make_response('Token missing sid and sub', status=400)

            # Invalidate sessions in Odoo
            session_store = root.session_store
            sessions_at_start = session_store.list()
            sessions_to_delete = []

            # We search for a user matching the sub if provided
            user_id = False
            if sub:
                 user = sudo_env['res.users'].sudo().search([('keycloak_sub', '=', sub)], limit=1)
                 if user:
                     user_id = user.id
                     _logger.debug("Back-channel logout: Found Odoo user %s for sub %s", user.login, sub)

            for session_id in sessions_at_start:
                try:
                    s = session_store.get(session_id)
                    # 1. Primary match: by Keycloak Session ID
                    if sid and s.get('keycloak_sid') == sid:
                        _logger.info("Back-channel logout: Matching session %s by sid %s", session_id, sid)
                        sessions_to_delete.append(s)
                    # 2. Secondary match: by Odoo UID (if sub is known and only sub is provided)
                    elif not sid and user_id and s.get('uid') == user_id:
                        _logger.info("Back-channel logout: Matching session %s by uid %s (sub %s)", session_id, user_id, sub)
                        sessions_to_delete.append(s)
                except Exception as e:
                    _logger.debug("Back-channel logout: Error reading session %s: %s", session_id, e)
                    continue

            deleted_count = 0
            for s in sessions_to_delete:
                try:
                    _logger.info("Back-channel logout: Terminating Odoo session %s", s.sid)
                    session_store.delete(s)
                    deleted_count += 1
                except Exception as e:
                    _logger.error("Back-channel logout: Failed to delete session %s: %s", s.sid, e)

            _logger.info("Back-channel logout processed: %d sessions terminated", deleted_count)
            return request.make_response('OK', status=200)

        except Exception as e:
            _logger.error("Back-channel logout processing error: %s", e)
            return request.make_response(str(e), status=400)
