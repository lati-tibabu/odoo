from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    benote_jwt_secret = fields.Char(
        string='Benote JWT Secret',
        config_parameter='benote.jwt_secret',
    )
