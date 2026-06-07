##############################################################################
# networking/main.tf
#
# Creates all network primitives needed by the Mitumba Shop Manager:
#   - VPC with DNS enabled
#   - One public subnet (EC2 lives here; no NAT gateway needed → free tier)
#   - Internet Gateway + route table
#   - Security group: SSH (restricted), HTTP 80, HTTPS 443
#
# To migrate to a different AWS account change only the values in
# terraform.tfvars (or the calling environment's variables.tf) — no code
# changes required.
##############################################################################

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-vpc"
  })
}

# ── Internet Gateway ────────────────────────────────────────────────────────

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-igw"
  })
}

# ── Public Subnet ───────────────────────────────────────────────────────────
# Single AZ is enough for a single-instance setup and avoids cross-AZ traffic
# costs.  Change availability_zone to suit your preferred AZ.

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-public-subnet"
  })
}

# ── Route Table ─────────────────────────────────────────────────────────────

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ── Security Group ──────────────────────────────────────────────────────────
# Best practice: restrict SSH to your own IP (set ssh_allowed_cidrs in vars).
# HTTP and HTTPS are open to the world so Nginx can serve the app and
# Let's Encrypt certificate renewal works.

resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "HTTP, HTTPS and SSH for Mitumba web server"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH — restrict to your IP in terraform.tfvars"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound so the instance can reach apt mirrors, PyPI, Cognito
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-web-sg"
  })
}
