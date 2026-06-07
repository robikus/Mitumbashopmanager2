##############################################################################
# cognito/outputs.tf
# Passed to the compute module so they land in the instance's .env file.
##############################################################################

output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "app_client_id" {
  description = "Cognito App Client ID (public, goes in .env)"
  value       = aws_cognito_user_pool_client.django.id
}

output "app_client_secret" {
  description = "Cognito App Client secret (sensitive — goes in .env)"
  value       = aws_cognito_user_pool_client.django.client_secret
  sensitive   = true
}

output "hosted_ui_url" {
  description = "Base URL of the Cognito hosted UI"
  value       = "https://${var.cognito_domain_prefix}.auth.${data.aws_region.current.name}.amazoncognito.com"
}

output "domain_prefix" {
  description = "Cognito domain prefix (passed to compute module)"
  value       = var.cognito_domain_prefix
}

# Read the current region so we can construct the hosted UI URL
data "aws_region" "current" {}
