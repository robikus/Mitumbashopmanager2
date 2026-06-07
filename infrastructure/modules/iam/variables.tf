##############################################################################
# iam/variables.tf
##############################################################################

variable "project_name" {
  description = "Short name prefix for all IAM resources"
  type        = string
}

variable "cognito_user_pool_arn" {
  description = "ARN of the Cognito User Pool to scope the EC2 Cognito policy. Pass an empty string to use '*' (less restrictive — useful before Cognito is created)."
  type        = string
  default     = ""
}

variable "create_admin_user" {
  description = "Set to true to create a named admin IAM user for Terraform/deployment operations. Set to false if you prefer to use an existing user or role."
  type        = bool
  default     = true
}

variable "common_tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default     = {}
}
