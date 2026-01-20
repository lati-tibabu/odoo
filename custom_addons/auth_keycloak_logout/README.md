# Keycloak OIDC Logout

[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-green.svg)](https://www.odoo.com/)

This Odoo module ensures that when users log out of Odoo, they are also logged out from Keycloak, providing a complete single sign-out experience across both systems.

## Features

- **Complete Logout**: Forces logout from both Odoo and Keycloak simultaneously.
- **Backchannel Logout**: Optionally invalidates refresh tokens server-side for enhanced security.
- **RP-Initiated Logout**: Redirects users to Keycloak's logout endpoint for browser-based logout.
- **Token Management**: Handles ID tokens and refresh tokens securely.
- **Fallback Handling**: Gracefully handles cases where tokens are unavailable.
- **Error Resilience**: Continues logout process even if Keycloak logout fails.

## Installation

1. Place the module in your Odoo addons directory.
2. Update your Odoo addons path if necessary.
3. Install the module through Odoo's Apps menu or using the command line:

```bash
odoo-bin -i auth_keycloak_logout
```

## Dependencies

- `web` - Odoo's web framework
- `auth_oauth` - Odoo's OAuth authentication module
- `auth_oidc` - OIDC-specific authentication features

## Configuration

### Prerequisites

Ensure you have a Keycloak OAuth provider configured in Odoo (see `auth_keycloak_login_redirect` module for setup details).

### Keycloak Configuration

1. **Client Settings**:
   - **Front Channel Logout**: Enabled (if using front-channel logout)
   - **Backchannel Logout URL**: Configure if using backchannel logout
   - **Logout Redirect URIs**: Add your Odoo base URL

2. **Realm Settings**:
   - Ensure logout endpoints are properly configured

## How It Works

1. **Session Destruction**: First destroys the Odoo session.
2. **Backchannel Logout** (Optional): Invalidates refresh tokens via server-to-server call.
3. **Browser Redirect**: Redirects user to Keycloak logout endpoint with proper parameters.
4. **Return to Odoo**: After Keycloak logout, redirects back to Odoo login page.

## Keycloak Logout Mechanisms

This module implements standard OpenID Connect (OIDC) logout mechanisms as supported by Keycloak. Understanding these mechanisms helps in configuring and troubleshooting the logout process.

### RP-Initiated Logout

**What it is**: The Relying Party (RP, in this case Odoo) initiates the logout by redirecting the user's browser to Keycloak's logout endpoint.

**How it works**:
1. User clicks logout in the application
2. Application destroys its local session
3. Application redirects browser to: `https://keycloak-domain/realms/realm-name/protocol/openid-connect/logout`
4. Keycloak logs out the user and optionally redirects back to the application

**Parameters**:
- `client_id`: The client identifier
- `post_logout_redirect_uri`: Where to redirect after logout
- `id_token_hint`: The ID token (optional, helps Keycloak identify the session)

**Pros**: Simple, works in all browsers, visible to user
**Cons**: Requires browser redirect

### Backchannel Logout

**What it is**: Server-to-server logout where the RP calls Keycloak's logout endpoint directly without browser involvement.

**How it works**:
1. Application makes HTTP POST request to Keycloak's logout endpoint
2. Includes refresh token or other credentials
3. Keycloak invalidates the session server-side
4. Application can then redirect the browser

**Endpoint**: Usually `https://keycloak-domain/realms/realm-name/protocol/openid-connect/logout`

**Pros**: No browser redirect needed, more secure for programmatic logout
**Cons**: Requires refresh token, may not log out browser sessions

### Front-Channel Logout

**What it is**: Keycloak initiates logout by redirecting the user's browser to logout URLs configured for each client.

**How it works**:
1. When logout is initiated, Keycloak redirects browser to client's logout URL
2. Client destroys its session
3. Client may redirect back to Keycloak or elsewhere

**Configuration**: Set in Keycloak client settings under "Logout Settings" > "Front Channel Logout"

**Pros**: Keycloak controls the logout flow
**Cons**: Requires all clients to handle logout redirects

### Implementation in This Module

This module primarily uses **RP-Initiated Logout** for the main logout flow, with optional **Backchannel Logout** for enhanced security. Front-Channel Logout can be configured in Keycloak for additional logout scenarios.

## Usage

The module works automatically once installed and configured. When users click "Logout" in Odoo, they'll be logged out from both systems.

## Troubleshooting

- **Logout not working**: Ensure OAuth provider is properly configured and enabled.
- **Tokens not found**: Check if users are logging in via OAuth and tokens are stored.
- **Redirect loops**: Verify Keycloak logout redirect URIs are correctly set.

## Security Considerations

- Tokens are handled securely and only used for logout purposes.
- Backchannel logout provides additional security by invalidating tokens server-side.
- All logout operations are logged for audit purposes.

## License

This module is licensed under the LGPL-3 License. See the LICENSE file for more details.

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the project repository.

## Support

For support, please check the Odoo community forums or the project's issue tracker.</content>
<parameter name="filePath">/home/lati/src/odoo18_debranded/custom_addons/auth_keycloak_logout/README.md