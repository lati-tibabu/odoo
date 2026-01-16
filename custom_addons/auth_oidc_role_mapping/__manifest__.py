{
    "name": "OIDC Role Mapping (Keycloak)",
    "version": "18.0.1.0.0",
    "category": "Authentication",
    "summary": "Automatically map OIDC roles from Keycloak to Odoo user groups",
    "description": """
OIDC Role Mapping for Odoo (Keycloak)
=======================================

This module extends Odoo's OAuth/OpenID Connect (OIDC) authentication to support
automatic authorization through role-to-group synchronization.

When users authenticate via an OIDC provider such as **Keycloak**,
the module extracts role information from the ID token and maps those roles to
Odoo user groups (`res.groups`). This enables centralized access
control in the Identity Provider while keeping authorization inside Odoo fully
automated and consistent.


Key Features
------------

- Supports OpenID Connect (OIDC) providers (tested with Keycloak)
- Extracts roles from configurable ID token claims
- Maps external IdP roles to Odoo user groups
- Additive group assignment (existing groups are preserved)
- Works with ID Token authentication flow
- Integrates directly into the OAuth Provider configuration UI
- Compatible with automatic user creation via `auth_signup`

Typical Use Cases
-----------------

- Centralized authorization management using Keycloak
- Role-based access control across multiple applications
- Eliminating manual group assignment in Odoo
- Enterprise SSO with consistent permission enforcement

Scope
-----

This module does **not** replace Odoo's native security model.
It augments it by synchronizing external Identity Provider roles into native
Odoo user groups.

""",
    "author": "Lati Tibabu",
    "website": "https://github.com/latitibabu",
    "license": "LGPL-3",
    "depends": [
        "base",
        "auth_oauth",
        "auth_oidc",
        "auth_signup",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/auth_oidc_provider_views.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
