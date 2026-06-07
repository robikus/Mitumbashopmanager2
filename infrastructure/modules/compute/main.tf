##############################################################################
# compute/main.tf
#
# Provisions the single EC2 instance that runs everything:
#   - Ubuntu 22.04 LTS (latest AMI looked up via data source)
#   - t2.micro (free tier: 750 h/month)
#   - Elastic IP so the DNS record survives instance stops
#   - SSH key pair (public key provided as variable)
#   - user_data bootstrap script (installs Nginx, Django, PostgreSQL)
##############################################################################

# ── Latest Ubuntu 22.04 LTS AMI ─────────────────────────────────────────────
# Using a data source keeps the AMI ID account- and region-agnostic.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS account

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── SSH Key Pair ─────────────────────────────────────────────────────────────
resource "aws_key_pair" "app" {
  key_name   = "${var.project_name}-key"
  public_key = var.ssh_public_key

  tags = var.common_tags
}

# ── IAM Instance Profile ─────────────────────────────────────────────────────
# Passed in from the IAM module so the EC2 instance can call AWS APIs
# (e.g. Cognito, SSM Parameter Store) without embedding long-lived credentials.

# ── EC2 Instance ─────────────────────────────────────────────────────────────
resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type  # defaults to t2.micro
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name               = aws_key_pair.app.key_name
  iam_instance_profile   = var.iam_instance_profile_name

  # Bootstrap script: installs packages and configures the server.
  # templatefile() fills in the DB credentials and Cognito details at plan time.
  user_data = templatefile("${path.module}/user_data.sh", {
    db_name                    = var.db_name
    db_user                    = var.db_user
    db_password                = var.db_password
    app_domain                 = var.app_domain
    django_secret_key          = var.django_secret_key
    cognito_domain             = var.cognito_domain_prefix
    cognito_region             = var.aws_region
    cognito_user_pool_id       = var.cognito_user_pool_id
    cognito_app_client_id      = var.cognito_app_client_id
    cognito_app_client_secret  = var.cognito_app_client_secret
  })

  # 20 GiB gp3 root volume — stays within free-tier 30 GiB allowance
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
    encrypted             = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-app-server"
  })

  # Replace the instance if user_data changes (i.e. new bootstrap config).
  # Comment this out if you manage the server with Ansible/SSH instead.
  lifecycle {
    create_before_destroy = true
  }
}

# ── Elastic IP ───────────────────────────────────────────────────────────────
# Ensures the public IP stays constant across stop/start cycles so your
# DNS A record doesn't break.
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-eip"
  })

  depends_on = [aws_instance.app]
}
