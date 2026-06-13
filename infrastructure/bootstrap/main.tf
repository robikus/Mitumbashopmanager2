##############################################################################
# bootstrap/main.tf
#
# Run this ONCE before using any other Terraform workspace.
# Creates two resources that all other workspaces depend on:
#
#   1. S3 bucket  — stores terraform.tfstate files (encrypted, versioned)
#   2. DynamoDB table — prevents two simultaneous `terraform apply` runs
#
# This workspace itself uses LOCAL state (stored in bootstrap/terraform.tfstate).
# That is intentional — it is safe to commit this file because it contains
# no secrets, only resource names and ARNs.
#
# Usage:
#   cd infrastructure/bootstrap
#   terraform init
#   terraform apply
#   # copy bucket_name output into environments/production/main.tf backend block
##############################################################################

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  # Intentionally no backend block — local state is correct here.
}

provider "aws" {
  region = var.aws_region
}

# ── Random suffix so the bucket name is globally unique ─────────────────────
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  bucket_name = "${var.project_name}-tfstate-${random_id.suffix.hex}"
}

# ── S3 Bucket ─────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "tfstate" {
  bucket = local.bucket_name

  # Prevent accidental deletion of state files
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name      = local.bucket_name
    Purpose   = "Terraform remote state"
    Project   = var.project_name
    ManagedBy = "terraform-bootstrap"
  }
}

# Versioning — lets you roll back to a previous state if something goes wrong
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption at rest — state files can contain secrets (DB passwords, etc.)
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access — state must never be public
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── DynamoDB Lock Table ────────────────────────────────────────────────────────
# Terraform uses this to hold a lock during apply so two laptops can't
# write state at the same time.
resource "aws_dynamodb_table" "tfstate_lock" {
  name         = "${var.project_name}-tfstate-lock"
  billing_mode = "PROVISIONED"
  read_capacity  = 1  # 1 of the 25 free RCU in the always-free DynamoDB tier
  write_capacity = 1  # 1 of the 25 free WCU
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "${var.project_name}-tfstate-lock"
    Purpose   = "Terraform state locking"
    Project   = var.project_name
    ManagedBy = "terraform-bootstrap"
  }
}
