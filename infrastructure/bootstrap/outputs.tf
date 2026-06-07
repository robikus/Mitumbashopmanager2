output "bucket_name" {
  description = "S3 bucket name — copy this into the backend block in environments/production/main.tf"
  value       = aws_s3_bucket.tfstate.id
}

output "dynamodb_table_name" {
  description = "DynamoDB table name — copy this into the backend block in environments/production/main.tf"
  value       = aws_dynamodb_table.tfstate_lock.name
}

output "aws_region" {
  description = "Region where the bucket and table were created"
  value       = var.aws_region
}

output "next_step" {
  value = <<-EOT
    Add this backend block to infrastructure/environments/production/main.tf:

      backend "s3" {
        bucket         = "${aws_s3_bucket.tfstate.id}"
        key            = "mitumba/production/terraform.tfstate"
        region         = "${var.aws_region}"
        encrypt        = true
        dynamodb_table = "${aws_dynamodb_table.tfstate_lock.name}"
      }

    Then run:  terraform init   (in environments/production/)
    Terraform will ask: "Do you want to copy existing state to the new backend?" → yes
  EOT
}
