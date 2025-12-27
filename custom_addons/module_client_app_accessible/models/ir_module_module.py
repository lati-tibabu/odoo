from odoo import fields, models

class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    client_app_accessible = fields.Boolean(string='Client App Accessible', default=False,
                                           help='Indicates if the module is accessible from the client application like react apps')
    
    def action_toggle_client_app_accessible(self):
        self.ensure_one()
        self.client_app_accessible = not self.client_app_accessible