from odoo import fields, models

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('chapa', 'Chapa')], 
        ondelete={'chapa': 'set default'}
    )
    chapa_secret_key = fields.Char(
        string="Chapa Secret Key",
        help="The Secret Key from your Chapa Dashboard (Settings > API)",
        required_if_provider='chapa',
        groups='base.group_system'
    )
    chapa_webhook_secret = fields.Char(
        string="Chapa Webhook Secret",
        help="The Secret Hash you set in Chapa Dashboard for Webhooks",
        groups='base.group_system'
    )

    def _get_supported_currencies(self):
        """ Chapa mainly supports ETB and USD. """
        self.ensure_one()
        if self.code == 'chapa':
            return self.env['res.currency'].search([('name', 'in', ['ETB', 'USD'])])
        return super()._get_supported_currencies()
