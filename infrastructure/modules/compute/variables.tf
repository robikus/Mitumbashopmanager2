##############################################################################
# compute/variables.tf
##############################################################################

variable "project_name" {
  description = "Short name prefix for all resources (e.g. 'mitumba')"
  type        = string
}

variable "aws_region" {
  description = "AWS region — must match the region of the subnet"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type. t2.micro is free-tier eligible."
  type        = string
  default     = "t2.micro"
}

variable "subnet_id" {
  description = "ID of the public subnet in which to launch the instance (from networking module)"
  type        = string
}

variable "security_group_id" {
  description = "ID of the security group to attach (from networking module)"
  type        = string
}

variable "ssh_public_key" {
  description = "Public SSH key content (the .pub file). Used to create an AWS key pair for SSH access."
  type        = string
  sensitive   = true
}

variable "iam_instance_profile_name" {
  description = "Name of the IAM instance profile to attach so the instance can call AWS APIs without static credentials"
  type        = string
}

# ── Database ─────────────────────────────────────────────────────────────────

variable "db_name" {
  description = "PostgreSQL database name created during bootstrap"
  type        = string
  default     = "mitumba_db"
}

variable "db_user" {
  description = "PostgreSQL role/user name"
  type        = string
  default     = "mitumba_user"
}

variable "db_password" {
  description = "PostgreSQL password — use a strong random string, store in Secrets Manager or tfvars (gitignored)"
  type        = string
  sensitive   = true
}

# ── Application ───────────────────────────────────────────────────────────────

variable "app_domain" {
  description = "Fully-qualified domain name for the app (e.g. app.example.com). Used in Nginx config and Cognito callback URLs."
  type        = string
}

variable "django_secret_key" {
  description = "Django SECRET_KEY — generate with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
  type        = string
  sensitive   = true
}

# ── Cognito (passed through to .env on the instance) ─────────────────────────

variable "cognito_domain_prefix" {
  description = "Cognito hosted UI domain prefix (the part before .auth.<region>.amazoncognito.com)"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
}

variable "cognito_app_client_id" {
  description = "Cognito App Client ID"
  type        = string
}

variable "cognito_app_client_secret" {
  description = "Cognito App Client Secret"
  type        = string
  sensitive   = true
}

variable "common_tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default     = {}
}
