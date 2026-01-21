# Keycloak Auth

JWT-based SSO integration for Keycloak.

## Features
- JWT Token validation (RS256/HS256)
- Automatic user creation/mapping via `keycloak_sub`
- Role synchronization (Admin/User mapping)
- **Session ID Tracking**: Captures Keycloak `sid` for session synchronization.

## Setup
1. Configure `keycloak.jwt_secret` in System Parameters.
2. Direct Keycloak to post to `/auth/sso/callback`.

## Session Synchronization
This module captures the Keycloak Session ID (`sid`) during login. For full session termination (logout), install the `auth_keycloak_logout` module.
