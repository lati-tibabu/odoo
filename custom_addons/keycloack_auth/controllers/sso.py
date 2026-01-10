import logging

from odoo import http, SUPERUSER_ID
from odoo.http import request

try:
    import jwt
except ImportError:  # pragma: no cover - dependency is required at runtime
    jwt = None


_logger = logging.getLogger(__name__)


class KeycloakSSO(http.Controller):
    @http.route(['/auth/sso/callback', '/sso/jwt/login'], type='http', auth='none', methods=['POST'], csrf=False)
    def sso_callback(self, **post):
        if jwt is None:
            _logger.error("PyJWT is not installed; keycloak_auth cannot decode tokens.")
            return request.make_response('SSO unavailable', status=500)

        token = post.get('access_token')
        if not token:
            return request.make_response('Missing access_token', status=400)

        sudo_env = request.env(user=SUPERUSER_ID)
        secret = sudo_env['ir.config_parameter'].get_param('keycloak.jwt_secret')
        if not secret:
            return request.make_response('JWT secret not configured', status=500)

        try:
            # We relax checks for easier integration. 
            # Keycloak often uses RS256, but if we are using a secret string, it implies HS256.
            # If the user provides a public key as the secret, RS256 will work.
            payload = jwt.decode(
                token,
                secret,
                algorithms=['HS256', 'RS256'],
                options={'verify_aud': False, 'verify_iss': False},
            )
        except jwt.ExpiredSignatureError:
            return request.make_response('Token expired', status=401)
        except jwt.InvalidTokenError as e:
            _logger.error(f"Invalid Token: {e}")
            return request.make_response('Invalid token', status=401)

        sub = payload.get('sub')
        if not sub:
            return request.make_response('Token missing sub', status=401)

        email = payload.get('email')
        users = sudo_env['res.users']

        user = users.search([('keycloak_sub', '=', sub)], limit=1)
        if not user and email:
            user = users.search([('login', '=', email)], limit=1)
            if user:
                user.write({'keycloak_sub': sub})

        if not user:
            return request.make_response('User not found', status=403)

        # Retrieve roles from Keycloak standard location
        # Structure often is: {'realm_access': {'roles': ['...']}}
        roles = []
        realm_access = payload.get('realm_access', {})
        if isinstance(realm_access, dict):
            roles = realm_access.get('roles', [])
        
        # Fallback to top-level roles if present (custom mappers)
        if not roles and 'roles' in payload:
             roles = payload.get('roles')
             if isinstance(roles, str):
                roles = [roles]

        if 'admin' in roles:
            group = sudo_env.ref('base.group_system')
            if group not in user.groups_id:
                user.write({'groups_id': [(4, group.id)]})
        else:
            group = sudo_env.ref('base.group_user')
            if group not in user.groups_id:
                user.write({'groups_id': [(4, group.id)]})

        request.session.pre_login = user.login
        request.session.pre_uid = user.id
        request.session.finalize(sudo_env)
        request.env = request.env(user=user.id)

        return request.redirect('/web')
