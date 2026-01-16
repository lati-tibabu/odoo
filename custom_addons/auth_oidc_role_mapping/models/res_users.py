import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        login = super()._auth_oauth_signin(provider, validation, params)
        if not login:
            return login

        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if oauth_provider.flow not in ("id_token", "id_token_code"):
            return login

        user = self.search([("login", "=", login)], limit=1)
        if not user:
            _logger.warning("OIDC: User not found for login %s", login)
            return login

        self._apply_oidc_mapping(user, oauth_provider, validation)
        return login

    def _apply_oidc_mapping(self, user, provider, validation):
        claim_path = provider.oidc_role_claim or ""
        roles = self._extract_claim(validation, claim_path)

        if not roles:
            _logger.info("OIDC: No roles found for %s", user.login)
            return

        if isinstance(roles, str):
            roles = [roles]

        groups = self._map_roles_to_groups(provider, roles)
        if groups:
            combined = user.groups_id | groups
            user.groups_id = [(6, 0, combined.ids)]

    def _extract_claim(self, payload, claim_path):
        if not claim_path:
            return None
        value = payload
        for part in claim_path.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value

    def _map_roles_to_groups(self, provider, roles):
        groups = self.env["res.groups"]
        if not provider.oidc_role_mapping_ids:
            _logger.info(
                "OIDC: No role mappings configured for provider %s", provider.name
            )
            return groups

        role_keys = [str(role) for role in roles]
        matched = self.env["auth.oidc.role.mapping"].search(
            [("provider_id", "=", provider.id), ("role", "in", role_keys)]
        )

        found_roles = matched.mapped("role")
        for role in role_keys:
            if role not in found_roles:
                _logger.warning("OIDC: No group mapping for role %s", role)

        groups |= matched.mapped("group_id")
        return groups
