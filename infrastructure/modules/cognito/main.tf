##############################################################################
# cognito/main.tf
#
# Sets up AWS Cognito for user authentication:
#   - User Pool: stores user accounts, handles sign-up/sign-in
#   - User Pool Domain: hosted UI login page at a Cognito-managed URL
#   - App Client: Django backend uses this to exchange auth codes for tokens
#
# Auth flow (Authorization Code Grant):
#   1. Browser → Cognito Hosted UI (login/register)
#   2. Cognito → Django callback URL with `code`
#   3. Django exchanges `code` for ID + Access + Refresh tokens
#   4. Django creates/updates the user in PostgreSQL and sets a session cookie
#
# Free tier: 50,000 Monthly Active Users at no charge (no expiry).
##############################################################################

resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-user-pool"

  # ── Username / sign-in options ────────────────────────────────────────────
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  username_configuration {
    case_sensitive = false
  }

  # ── Password policy ────────────────────────────────────────────────────────
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = false
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  # ── MFA — optional SMS/TOTP (disabled by default to keep free tier) ────────
  mfa_configuration = "OFF"

  # ── Email verification ─────────────────────────────────────────────────────
  # Uses Cognito's built-in email (limited to 50/day; use SES in production)
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Mitumba Shop — Your verification code"
    email_message        = "Your Mitumba Shop verification code is: {####}"
  }

  # ── Standard attributes required at sign-up ───────────────────────────────
  schema {
    name                     = "email"
    attribute_data_type      = "String"
    required                 = true
    mutable                  = true
    string_attribute_constraints {
      min_length = 5
      max_length = 254
    }
  }

  # ── Account recovery ──────────────────────────────────────────────────────
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # ── Admin-created users can sign themselves in ────────────────────────────
  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-user-pool"
  })
}

# ── Hosted UI Domain ─────────────────────────────────────────────────────────
# URL: https://<domain_prefix>.auth.<region>.amazoncognito.com
# Using the free Cognito subdomain (custom domains require ACM + extra setup).
resource "aws_cognito_user_pool_domain" "main" {
  domain       = var.cognito_domain_prefix
  user_pool_id = aws_cognito_user_pool.main.id
}

# ── App Client ───────────────────────────────────────────────────────────────
# Used by the Django backend to perform the OAuth2 token exchange.
resource "aws_cognito_user_pool_client" "django" {
  name         = "${var.project_name}-django-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Required for Authorization Code + PKCE flow used by server-side Django
  generate_secret = true

  # Allowed OAuth flows
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["email", "openid", "profile"]

  # Redirect URLs must exactly match what Django sends.
  # Add http://localhost:8000/auth/callback/ for local development.
  callback_urls = concat(
    ["https://${var.app_domain}/auth/callback/"],
    var.extra_callback_urls
  )

  logout_urls = [
    "https://${var.app_domain}/auth/logout/",
  ]

  supported_identity_providers = ["COGNITO"]

  # Token validity
  access_token_validity  = 1   # hours
  id_token_validity      = 1   # hours
  refresh_token_validity = 30  # days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # Prevent user existence errors leaking during auth (security best practice)
  prevent_user_existence_errors = "ENABLED"

  # Enable SRP and USER_PASSWORD_AUTH for API-based flows (used by admin CLI)
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
  ]
}
