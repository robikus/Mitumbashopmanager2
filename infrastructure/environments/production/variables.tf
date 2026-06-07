##############################################################################
# environments/production/variables.tf
# All account-specific and secret values are declared here.
# Actual values go in terraform.tfvars (gitignored).
##############################################################################

# ── General ───────────────────────────────────────────────────────────────────

variable "project_name" {
  description = "Short name used as prefix for all resources (e.g. 'mitumba'). Change when deploying to a new account to avoid name conflicts."
  type        = string
  default     = "mitumba"
}

variable "aws_region" {
  description = "AWS region to deploy all resources"
  type        = string
  default     = "us-east-1"
}

variable "owner_email" {
  description = "Email of the person/team that owns this deployment — added as a tag for cost attribution"
  type        = string
}

# ── Networking ────────────────────────────────────────────────────────────────

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "ssh_allowed_cidrs" {
  description = "Restrict SSH to your IP (e.g. [\"203.0.113.10/32\"]). Default opens to the world — change before going live."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ── Compute ───────────────────────────────────────────────────────────────────

variable "instance_type" {
  description = "EC2 instance type. t2.micro is free-tier eligible."
  type        = string
  default     = "t2.micro"
}

variable "ssh_public_key" {
  description = "Content of your SSH public key file (e.g. ~/.ssh/id_rsa.pub). Required for SSH access."
  type        = string
  sensitive   = true
}

variable "app_domain" {
  description = "FQDN for the application (e.g. shop.example.com). Create an A record pointing at the Elastic IP after deploy."
  type        = string
}

variable "django_secret_key" {
  description = "Django SECRET_KEY. Generate with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
  type        = string
  sensitive   = true
}

# ── Database ──────────────────────────────────────────────────────────────────

variable "db_name" {
  type    = string
  default = "mitumba_db"
}

variable "db_user" {
  type    = string
  default = "mitumba_user"
}

variable "db_password" {
  description = "PostgreSQL password. Use a strong random string (min 20 chars)."
  type        = string
  sensitive   = true
}

# ── Cognito ───────────────────────────────────────────────────────────────────

variable "cognito_domain_prefix" {
  description = "Globally unique prefix for the Cognito hosted UI subdomain (e.g. 'mitumba-shop-yourname')"
  type        = string
}

variable "cognito_extra_callback_urls" {
  description = "Additional OAuth2 callback URLs (e.g. localhost for dev)"
  type        = list(string)
  default     = ["http://localhost:8000/auth/callback/"]
}

# ── IAM ───────────────────────────────────────────────────────────────────────

variable "create_admin_user" {
  description = "Create an admin IAM user for Terraform operations. Set false if you already have a suitable user/role."
  type        = bool
  default     = true
}
