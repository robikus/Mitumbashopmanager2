variable "project_name" {
  description = "Short project name used as a prefix for the bucket and table names"
  type        = string
  default     = "mitumba"
}

variable "aws_region" {
  description = "AWS region where the S3 bucket and DynamoDB table are created. Use the same region as your main deployment."
  type        = string
  default     = "us-east-1"
}
