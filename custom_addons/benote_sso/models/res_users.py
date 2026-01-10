from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    benote_sub = fields.Char(string='Benote UUID', index=True, copy=False)

    _sql_constraints = [
        ('benote_sub_unique', 'unique(benote_sub)', 'The Benote UUID must be unique.'),
    ]
