import logging
import requests
from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    oauth_id_token = fields.Char(string="OAuth ID Token", copy=False)
    oauth_refresh_token = fields.Char(string="OAuth Refresh Token", copy=False)

    def _auth_oauth_get_tokens_auth_code_flow(self, oauth_provider, params):
        """ Override to capture refresh_token as well """
        # We need to call the same logic as auth_oidc but capture more
        # Since we can't easily call super() and get the response_json, we might have to re-implement or 
        # just accept that we might fetch it twice if we are not careful.
        # However, we can just call the super and hope it's enough, 
        # but auth_oidc returns a tuple of 2 elements, we want 3.
        
        # Actually, let's just override it to capture the refresh token.
        code = params.get("code")
        auth = None
        if oauth_provider.client_secret:
            auth = (oauth_provider.client_id, oauth_provider.client_secret)
        
        # We use the same parameters as auth_oidc
        response = requests.post(
            oauth_provider.token_endpoint,
            data=dict(
                client_id=oauth_provider.client_id,
                grant_type="authorization_code",
                code=code,
                code_verifier=oauth_provider.code_verifier,
                redirect_uri=request.httprequest.url_root + "auth_oauth/signin",
            ),
            auth=auth,
            timeout=10,
        )
        response.raise_for_status()
        response_json = response.json()
        
        # Store refresh token in params so it can be picked up in _auth_oauth_signin
        params['refresh_token'] = response_json.get("refresh_token")
        
        return response_json.get("access_token"), response_json.get("id_token")

    def _auth_oauth_signin(self, provider, validation, params):
        login = super(ResUsers, self)._auth_oauth_signin(provider, validation, params)
        if login:
            user = self.sudo().search([('login', '=', login), ('id', '!=', 1)], limit=1)
            if user:
                id_token = params.get('id_token')
                refresh_token = params.get('refresh_token')
                
                user.write({
                    'oauth_id_token': id_token,
                    'oauth_refresh_token': refresh_token,
                })
                
                if request:
                    if id_token:
                        request.session['id_token'] = id_token
                    if refresh_token:
                        request.session['refresh_token'] = refresh_token
        return login
