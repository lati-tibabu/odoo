# Keycloak Login Redirect

[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-green.svg)](https://www.odoo.com/)

This Odoo module automatically redirects users to Keycloak for authentication when they access the Odoo login page, leveraging Odoo's built-in OAuth/OIDC authentication flow.

## Features

- **Automatic Redirect**: Seamlessly redirects users from Odoo's login page to Keycloak without manual intervention.
- **Safety Bypasses**: Includes bypass mechanisms for error handling and direct access (e.g., `?no_redirect=1`).
- **Dynamic Provider Detection**: Automatically detects and uses the enabled Keycloak OAuth provider.
- **State Management**: Properly handles OAuth state parameters for secure authentication flow.
- **Fallback Support**: Falls back to standard Odoo login if no Keycloak provider is configured.

## Installation

1. Place the module in your Odoo addons directory.
2. Update your Odoo addons path if necessary.
3. Install the module through Odoo's Apps menu or using the command line:

```bash
odoo-bin -i auth_keycloak_login_redirect
```

## Dependencies

- `web` - Odoo's web framework
- `auth_oauth` - Odoo's OAuth authentication module

## Configuration

### Keycloak Setup

1. **Create an OAuth Provider in Odoo**:
   - Go to **Settings > Users & Companies > OAuth Providers**
   - Create a new provider with:
     - **Provider name**: Keycloak (case-insensitive)
     - **Auth Flow**: OpenID Connect (Authorization Code Flow)
     - **Client ID**: Your Keycloak client ID
     - **Client Secret**: Your Keycloak client secret
     - **Authorization URL**: `https://your-keycloak-domain/realms/your-realm/protocol/openid-connect/auth`
     - **Token URL**: `https://your-keycloak-domain/realms/your-realm/protocol/openid-connect/token`
     - **UserInfo URL**: `https://your-keycloak-domain/realms/your-realm/protocol/openid-connect/userinfo`
     - **Scope**: `openid profile email`
     - **Enabled**: ✅

2. **Keycloak Client Configuration**:
   - **Valid Redirect URIs**: Add your Odoo base URL + `/auth_oauth/signin`
     - Example: `http://localhost:8069/auth_oauth/signin`

### Usage

Once configured, users accessing `/web/login` will be automatically redirected to Keycloak. After successful authentication, they'll be logged into Odoo.

To bypass the redirect (e.g., for admin access), append `?no_redirect=1` to the login URL.

## Troubleshooting

- **No redirect happening**: Ensure the OAuth provider is named "Keycloak" and is enabled.
- **Authentication errors**: Check Keycloak client configuration and redirect URIs.
- **Loop issues**: Use `?no_redirect=1` to access standard login.

## License

This module is licensed under the LGPL-3 License. See the LICENSE file for more details.

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the project repository.

## Support

For support, please check the Odoo community forums or the project's issue tracker.</content>
<parameter name="filePath">/home/lati/src/odoo18_debranded/custom_addons/auth_keycloak_login_redirect/README.md