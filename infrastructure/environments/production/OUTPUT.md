Outputs:

admin_iam_user = "mitumba-admin"
cognito_app_client_id = "1fabgguo8k5krsdpsc9b4pbfgp"
cognito_app_client_secret = <sensitive>
cognito_hosted_ui_url = "https://mitumba-shop-yourname.auth.eu-central-1.amazoncognito.com"
cognito_user_pool_id = "eu-central-1_nrMzlxwlB"
ec2_instance_id = "i-0b1454ad008f8603d"
next_steps = <<EOT
1. Create DNS A record:  shop.example.com  →  63.183.43.81
2. SSH: ssh ubuntu@63.183.43.81
3. Deploy app: git clone https://your-repo /opt/mitumba/backend
4. Run migrations: sudo -u www-data /opt/mitumba/venv/bin/python /opt/mitumba/backend/manage.py migrate
5. Collect static: sudo -u www-data /opt/mitumba/venv/bin/python /opt/mitumba/backend/manage.py collectstatic --no-input
6. Start app: sudo systemctl start mitumba
7. Get TLS cert: sudo certbot --nginx -d shop.example.com
8. Test login at: https://mitumba-shop-yourname.auth.eu-central-1.amazoncognito.com

EOT
server_dns = "ec2-63-183-43-81.eu-central-1.compute.amazonaws.com"
server_ip = "63.183.43.81"