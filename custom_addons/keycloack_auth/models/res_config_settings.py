from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    keycloak_jwt_secret = fields.Char(
        string='Keycloak JWT Secret',
        config_parameter='keycloak.jwt_secret',
    )
