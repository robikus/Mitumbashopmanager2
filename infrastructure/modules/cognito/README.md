# Module: cognito

Configures AWS Cognito as the identity provider for Mitumba Shop Manager.

## What is created

| Resource | Purpose |
|---|---|
| `aws_cognito_user_pool` | Stores user accounts; handles sign-up, verification, password reset |
| `aws_cognito_user_pool_domain` | Hosted login UI at `<prefix>.auth.<region>.amazoncognito.com` |
| `aws_cognito_user_pool_client` | OAuth2 app client used by Django backend |

## Authentication flow

```
Browser
  │
  │  GET / (unauthenticated)
  ▼
Django
  │  No valid session → redirect to Cognito hosted UI
  ▼
Cognito Hosted UI  (https://<prefix>.auth.<region>.amazoncognito.com/login)
  │  User logs in / registers
  │  Cognito redirects to callback URL with ?code=...
  ▼
Django /auth/callback/
  │  POST to Cognito token endpoint to exchange code for tokens
  │  Validate ID token (JWT signature + claims)
  │  Create/update User record in PostgreSQL (keyed on Cognito `sub`)
  │  Set Django session cookie
  ▼
Browser — authenticated, SPA takes over
```

## Free tier

Cognito free tier: **50,000 MAUs** — no expiry.  The hosted UI is free.
SES email sending is free up to 50 emails/day using the Cognito default
sender; upgrade to SES for higher volumes.

## Migrating to a different AWS account

Change `cognito_domain_prefix` (must be globally unique) and `app_domain` in
`terraform.tfvars`.  No code changes required.  After running `terraform apply`
in the new account, update the EC2 instance's `/opt/mitumba/.env` with the new
`COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, and
`COGNITO_APP_CLIENT_SECRET` values (available via `terraform output`).

## Inputs

| Name | Description | Default |
|---|---|---|
| `project_name` | Resource name prefix | — |
| `cognito_domain_prefix` | Globally unique subdomain prefix | — |
| `app_domain` | App FQDN (for callback URL) | — |
| `extra_callback_urls` | Extra OAuth2 callback URLs | `["http://localhost:8000/auth/callback/"]` |

## Outputs

| Name | Description |
|---|---|
| `user_pool_id` | User Pool ID |
| `app_client_id` | App Client ID |
| `app_client_secret` | App Client Secret (sensitive) |
| `hosted_ui_url` | Login page URL |
| `domain_prefix` | Domain prefix (passed to compute module) |
