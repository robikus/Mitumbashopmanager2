##############################################################################
# networking/variables.tf
##############################################################################

variable "project_name" {
  description = "Short name used as a prefix for every resource (e.g. 'mitumba'). Change this to avoid name collisions when deploying to a new account."
  type        = string
}

variable "aws_region" {
  description = "AWS region in which to create the subnet (e.g. 'us-east-1'). The subnet is placed in the first AZ of this region."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC. Default 10.0.0.0/16 gives 65 536 addresses."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet. Must be within vpc_cidr."
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_allowed_cidrs" {
  description = "CIDRs allowed to reach port 22. Restrict to your own IP for security (e.g. [\"203.0.113.10/32\"])."
  type        = list(string)
  default     = ["0.0.0.0/0"] # open by default; override in tfvars
}

variable "common_tags" {
  description = "Tags applied to every resource created by this module. Merge project, environment, and owner tags here."
  type        = map(string)
  default     = {}
}
