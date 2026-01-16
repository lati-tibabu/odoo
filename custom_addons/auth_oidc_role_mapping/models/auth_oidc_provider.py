from odoo import models, fields

class AuthOAuthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    oidc_role_claim = fields.Char(
        string="OIDC Role Claim Path",
        default="realm_access.roles",
        help="Claim path in the ID token containing roles (e.g., realm_access.roles or groups)."
    )
    oidc_role_mapping_ids = fields.One2many(
        "auth.oidc.role.mapping",
        "provider_id",
        string="OIDC Role Mappings",
        help="Map OIDC roles to Odoo groups for this provider.",
    )
