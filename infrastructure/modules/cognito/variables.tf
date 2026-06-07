##############################################################################
# cognito/variables.tf
##############################################################################

variable "project_name" {
  description = "Short name prefix for resource names"
  type        = string
}

variable "cognito_domain_prefix" {
  description = "Subdomain prefix for the Cognito hosted UI. Must be globally unique across all AWS accounts. Example: 'mitumba-shop-prod'. The hosted UI URL will be https://<prefix>.auth.<region>.amazoncognito.com"
  type        = string
}

variable "app_domain" {
  description = "FQDN of the application (e.g. app.example.com). Used to construct the OAuth2 callback URL."
  type        = string
}

variable "extra_callback_urls" {
  description = "Additional OAuth2 callback URLs to allow (e.g. localhost for development)"
  type        = list(string)
  default     = ["http://localhost:8000/auth/callback/"]
}

variable "common_tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default     = {}
}
