##############################################################################
# environments/production/outputs.tf
# Run `terraform output` after apply to get the values you need.
##############################################################################

output "server_ip" {
  description = "Elastic IP — create your DNS A record pointing here"
  value       = module.compute.public_ip
}

output "server_dns" {
  description = "AWS-assigned public DNS for the Elastic IP"
  value       = module.compute.public_dns
}

output "cognito_hosted_ui_url" {
  description = "Cognito hosted login/register page URL"
  value       = module.cognito.hosted_ui_url
}

output "cognito_user_pool_id" {
  description = "User Pool ID — needed in the app's .env"
  value       = module.cognito.user_pool_id
}

output "cognito_app_client_id" {
  description = "App Client ID — needed in the app's .env"
  value       = module.cognito.app_client_id
}

output "cognito_app_client_secret" {
  description = "App Client Secret — needed in the app's .env (sensitive)"
  value       = module.cognito.app_client_secret
  sensitive   = true
}

output "admin_iam_user" {
  description = "Name of the admin IAM user (if created)"
  value       = module.iam.admin_user_name
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = module.compute.instance_id
}

output "next_steps" {
  description = "Post-deployment checklist"
  value       = <<-EOT
    1. Create DNS A record:  ${var.app_domain}  →  ${module.compute.public_ip}
    2. SSH: ssh ubuntu@${module.compute.public_ip}
    3. Deploy app: git clone https://your-repo /opt/mitumba/backend
    4. Run migrations: sudo -u www-data /opt/mitumba/venv/bin/python /opt/mitumba/backend/manage.py migrate
    5. Collect static: sudo -u www-data /opt/mitumba/venv/bin/python /opt/mitumba/backend/manage.py collectstatic --no-input
    6. Start app: sudo systemctl start mitumba
    7. Get TLS cert: sudo certbot --nginx -d ${var.app_domain}
    8. Test login at: ${module.cognito.hosted_ui_url}
  EOT
}
