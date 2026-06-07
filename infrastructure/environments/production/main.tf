##############################################################################
# environments/production/main.tf
#
# Top-level composition of all modules for the production environment.
#
# To deploy to a different AWS account:
#   1. Change aws_region, project_name, app_domain, cognito_domain_prefix
#      and secrets in terraform.tfvars
#   2. Ensure ~/.aws/credentials (or environment variables) point at the
#      new account
#   3. terraform init && terraform plan && terraform apply
#
# State backend: local by default.  To use S3 (recommended for teams),
# uncomment the backend block below and create the bucket + DynamoDB table
# first.
##############################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # ── Optional: remote state backend (recommended for teams) ───────────────
  # Uncomment and fill in to store state in S3 instead of locally.
  # Create the bucket and DynamoDB table manually (or via a separate bootstrap
  # workspace) before enabling this.
  #
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "mitumba/production/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = "production"
    ManagedBy   = "terraform"
    Owner       = var.owner_email
  }
}

# ── 1. IAM (created first — instance profile needed by compute) ─────────────
module "iam" {
  source = "../../modules/iam"

  project_name          = var.project_name
  cognito_user_pool_arn = module.cognito.user_pool_arn
  create_admin_user     = var.create_admin_user
  common_tags           = local.common_tags

  depends_on = [module.cognito]
}

# ── 2. Networking ─────────────────────────────────────────────────────────────
module "networking" {
  source = "../../modules/networking"

  project_name       = var.project_name
  aws_region         = var.aws_region
  vpc_cidr           = var.vpc_cidr
  public_subnet_cidr = var.public_subnet_cidr
  ssh_allowed_cidrs  = var.ssh_allowed_cidrs
  common_tags        = local.common_tags
}

# ── 3. Cognito ────────────────────────────────────────────────────────────────
module "cognito" {
  source = "../../modules/cognito"

  project_name          = var.project_name
  cognito_domain_prefix = var.cognito_domain_prefix
  app_domain            = var.app_domain
  extra_callback_urls   = var.cognito_extra_callback_urls
  common_tags           = local.common_tags
}

# ── 4. Compute ────────────────────────────────────────────────────────────────
module "compute" {
  source = "../../modules/compute"

  project_name              = var.project_name
  aws_region                = var.aws_region
  instance_type             = var.instance_type
  subnet_id                 = module.networking.public_subnet_id
  security_group_id         = module.networking.web_security_group_id
  ssh_public_key            = var.ssh_public_key
  iam_instance_profile_name = module.iam.ec2_instance_profile_name

  db_name     = var.db_name
  db_user     = var.db_user
  db_password = var.db_password

  app_domain        = var.app_domain
  django_secret_key = var.django_secret_key

  cognito_domain_prefix       = module.cognito.domain_prefix
  cognito_user_pool_id        = module.cognito.user_pool_id
  cognito_app_client_id       = module.cognito.app_client_id
  cognito_app_client_secret   = module.cognito.app_client_secret

  common_tags = local.common_tags

  depends_on = [module.networking, module.iam, module.cognito]
}
