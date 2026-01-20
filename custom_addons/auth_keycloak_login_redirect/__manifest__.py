{
    "name": "Keycloak Login Redirect",
    "version": "18.0.1.0.0",
    "category": "Authentication",
    "summary": "Redirect Odoo login to Keycloak (OIDC)",
    "description": """
Automatically redirects the Odoo login page to Keycloak
using Odoo's OAuth/OIDC authentication flow.
""",
    "depends": [
        "web",
        "auth_oauth",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
