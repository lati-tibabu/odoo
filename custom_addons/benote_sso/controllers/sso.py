import logging

from odoo import http, SUPERUSER_ID
from odoo.http import request

try:
    import jwt
except ImportError:  # pragma: no cover - dependency is required at runtime
    jwt = None


_logger = logging.getLogger(__name__)


class BenoteSSO(http.Controller):
    @http.route(['/auth/sso/callback', '/sso/jwt/login'], type='http', auth='none', methods=['POST'], csrf=False)
    def sso_callback(self, **post):
        if jwt is None:
            _logger.error("PyJWT is not installed; benote_sso cannot decode tokens.")
            return request.make_response('SSO unavailable', status=500)

        token = post.get('access_token')
        if not token:
            return request.make_response('Missing access_token', status=400)

        sudo_env = request.env(user=SUPERUSER_ID)
        secret = sudo_env['ir.config_parameter'].get_param('benote.jwt_secret')
        if not secret:
            return request.make_response('JWT secret not configured', status=500)

        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=['HS256'],
                audience='odoo',
                issuer='benote-auth',
            )
        except jwt.ExpiredSignatureError:
            return request.make_response('Token expired', status=401)
        except jwt.InvalidTokenError:
            return request.make_response('Invalid token', status=401)

        sub = payload.get('sub')
        if not sub:
            return request.make_response('Token missing sub', status=401)

        email = payload.get('email')
        users = sudo_env['res.users']

        user = users.search([('benote_sub', '=', sub)], limit=1)
        if not user and email:
            user = users.search([('login', '=', email)], limit=1)
            if user:
                user.write({'benote_sub': sub})

        if not user:
            return request.make_response('User not found', status=403)

        roles = payload.get('roles') or []
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
