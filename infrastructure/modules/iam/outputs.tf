##############################################################################
# iam/outputs.tf
##############################################################################

output "ec2_instance_profile_name" {
  description = "Name of the IAM instance profile — pass to the compute module"
  value       = aws_iam_instance_profile.ec2_app.name
}

output "ec2_role_arn" {
  description = "ARN of the EC2 application role"
  value       = aws_iam_role.ec2_app.arn
}

output "admin_user_name" {
  description = "Name of the admin IAM user (empty if create_admin_user = false)"
  value       = var.create_admin_user ? aws_iam_user.admin[0].name : ""
}
