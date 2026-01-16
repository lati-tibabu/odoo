# OIDC Role Mapping Module

## Overview
The `auth_oidc_role_mapping` module extends Odoo's OAuth/OIDC authentication capabilities. Its primary purpose is to automate user permission management by synchronizing roles defined in an external Identity Provider (idP) (like Keycloak, Auth0, or Azure AD) with Odoo's internal User Groups.

When a user logs in via OIDC, this module intercepts the authentication flow, extracts role information from the ID token, and automatically assigns the corresponding Odoo groups to the user.

## Module Structure
```
auth_oidc_role_mapping/
├── __init__.py                 # Package initialization
├── __manifest__.py             # Odoo module manifest (dependencies, data)
├── README.md                   # Documentation
├── models/                     # Python logic
│   ├── __init__.py
│   ├── auth_oidc_provider.py   # Extends auth.oauth.provider
│   ├── auth_oidc_role_mapping.py # New model for mapping configuration
│   └── res_users.py            # Extends res.users logic
├── security/
│   └── ir.model.access.csv     # Access rights for the new model
└── views/
    └── auth_oidc_provider_views.xml # UI extensions for Provider settings
```

## Technical Architecture

### 1. Data Models

#### `auth.oidc.role.mapping` (New Model)
A configuration model that links an OIDC role string to an Odoo group.
- **Fields**:
  - `provider_id`: Many2one to `auth.oauth.provider`.
  - `role`: Char. The exact string value of the role returned by the IdP (e.g., "finance_manager").
  - `group_id`: Many2one to `res.groups`. The Odoo group to assign (e.g., "Invoicing / Administrator").

#### `auth.oauth.provider` (Extension)
Extends the standard OAuth provider to support role mapping configuration.
- **New Fields**:
  - `oidc_role_claim`: Char. The JSON path to find roles in the ID token (e.g., `realm_access.roles`).
  - `oidc_role_mapping_ids`: One2many. Link to the mapping rules.

### 2. Logic Flow & Methods

The core logic resides in `res.users`.

#### `_auth_oauth_signin(provider, validation, params)`
- **Overrides**: The standard Odoo OAuth sign-in method.
- **Process**:
  1. Calls `super()` to perform standard login/creation.
  2. Checks if the provider is configured for ID token flow.
  3. Calls `_apply_oidc_mapping` to sync groups.

#### `_apply_oidc_mapping(user, provider, validation)`
- Orchestrates the mapping process.
- Extracts roles using `_extract_claim`.
- Resolves Odoo groups using `_map_roles_to_groups`.
- Writes the new groups to `user.groups_id`. Note: This implementation is **additive**; it adds mapped groups but does not remove existing ones.

#### `_extract_claim(payload, claim_path)`
- Helper utility to traverse the nested JSON dictionary of the ID Token using dot notation (e.g., `realm_access` -> `roles`).

## Dependencies
- `base`: Core Odoo.
- `auth_oauth`: Standard OAuth2 support.
- `auth_oidc`: (Implied) OpenID Connect support.
- `auth_signup`: User creation flows.

## Access Rights
- The module adds access rules in `ir.model.access.csv` to ensure that System Administrators can configure the mappings.

## Configuration Guide
1. Navigate to **Settings > Users & Companies > OAuth Providers**.
2. Open an OIDC compatible provider (e.g., Keycloak).
3. Ensure the **Flow** is set to `ID Token`.
4. Locate the **OIDC Role Mapping** settings.
   - **OIDC Role Claim Path**: Set string path to the roles in the token (default: `realm_access.roles`).
   - **Mappings**: Add lines mapping IdP Role Names to Odoo Groups.
