from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.web.controllers.home import Home
import json
import werkzeug.urls

class KeycloakHome(Home):
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        
        # 1. Safety bypass: ?no_redirect=1 or errors
        if kw.get('no_redirect') or kw.get('oauth_error') or kw.get('error'):
            return super(KeycloakHome, self).web_login(redirect=redirect, **kw)

        # 2. Skip if already logged in or if it's a POST request
        if request.session.uid or request.httprequest.method == 'POST':
            return super(KeycloakHome, self).web_login(redirect=redirect, **kw)

        # 3. Dynamic Provider Lookup
        provider = request.env['auth.oauth.provider'].sudo().search([
            ('name', '=ilike', 'keycloak'),
            ('enabled', '=', True)
        ], limit=1)

        if provider:
            # Build the return_url - Keycloak MUST have this exact URL in 'Valid Redirect URIs'
            # Usually: http://localhost:8069/auth_oauth/signin
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return_url = werkzeug.urls.url_join(base_url, '/auth_oauth/signin')
            
            # Prepare redirect target for after login
            if not redirect:
                redirect = '/web'
            
            # Construct State
            state = {
                'd': request.session.db,
                'p': provider.id,
                'r': werkzeug.urls.url_quote(redirect),
            }
            
            params = {
                'response_type': 'code', # Use 'token' if you are using Implicit Flow
                'client_id': provider.client_id,
                'redirect_uri': return_url,
                'scope': provider.scope or 'openid profile email',
                'state': json.dumps(state),
            }
            
            auth_link = "%s?%s" % (provider.auth_endpoint, werkzeug.urls.url_encode(params))
            return request.redirect(auth_link, local=False)

        return super(KeycloakHome, self).web_login(redirect=redirect, **kw)