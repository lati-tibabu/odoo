from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    keycloak_sub = fields.Char(string='Keycloak UUID', index=True, copy=False)

    _sql_constraints = [
        ('keycloak_sub_unique', 'unique(keycloak_sub)', 'The Keycloak UUID must be unique.'),
    ]
