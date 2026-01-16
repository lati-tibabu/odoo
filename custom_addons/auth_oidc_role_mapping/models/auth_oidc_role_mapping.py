from odoo import fields, models


class AuthOidcRoleMapping(models.Model):
    _name = "auth.oidc.role.mapping"
    _description = "OIDC Role to Odoo Group Mapping"
    _order = "role, id"

    provider_id = fields.Many2one(
        "auth.oauth.provider",
        string="OAuth Provider",
        required=True,
        ondelete="cascade",
    )
    role = fields.Char(required=True)
    group_id = fields.Many2one("res.groups", string="Odoo Group", required=True)
