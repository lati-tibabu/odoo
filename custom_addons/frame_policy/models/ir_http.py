from odoo import models
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _post_dispatch(cls, response):
        super()._post_dispatch(response)
        
        # We only care about main document requests primarily, but applying globally is safer for iframes.
        # Check if parameter is set
        # Using sud() to ensure we can read the param even if not logged in (e.g. login page)
        frame_ancestors = request.env['ir.config_parameter'].sudo().get_param('web.frame_ancestors', '')
        
        if frame_ancestors:
            # 1. Remove X-Frame-Options (it conflicts with frame-ancestors in some scenarios or is too restrictive)
            if 'X-Frame-Options' in response.headers:
                response.headers.pop('X-Frame-Options', None)
            
            # 2. Update Content-Security-Policy
            # We preserve existing policies but replace frame-ancestors
            current_csp = response.headers.get('Content-Security-Policy', '')
            
            new_directive = f"frame-ancestors 'self' {frame_ancestors}"
            
            if current_csp:
                # Split and filter out existing frame-ancestors
                directives = [d.strip() for d in current_csp.split(';') if d.strip()]
                directives = [d for d in directives if not d.lower().startswith('frame-ancestors')]
                directives.append(new_directive)
                response.headers['Content-Security-Policy'] = '; '.join(directives)
            else:
                # No CSP exists, create one
                response.headers['Content-Security-Policy'] = new_directive
