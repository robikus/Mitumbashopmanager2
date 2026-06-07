##############################################################################
# iam/main.tf
#
# Creates two IAM identities:
#
# 1. EC2 Instance Role + Profile
#    Allows the EC2 instance to call specific AWS APIs without embedding
#    long-lived access keys on the server.
#    Permissions: read Cognito user pool info + read SSM parameters
#    (for future secret rotation via Parameter Store).
#
# 2. Admin IAM User
#    Human operator account for managing infrastructure (Terraform runs,
#    initial deploys).  No console access by default — add to the
#    Admin group to grant it.
#
##############################################################################

# ── EC2 Instance Role ─────────────────────────────────────────────────────────

resource "aws_iam_role" "ec2_app" {
  name        = "${var.project_name}-ec2-app-role"
  description = "Role assumed by the Mitumba app EC2 instance"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.common_tags
}

# Minimal Cognito permissions — read pool configuration and verify tokens
resource "aws_iam_policy" "ec2_cognito" {
  name        = "${var.project_name}-ec2-cognito-policy"
  description = "Allows EC2 to read Cognito user pool info (for token validation)"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CognitoReadOnly"
        Effect = "Allow"
        Action = [
          "cognito-idp:DescribeUserPool",
          "cognito-idp:DescribeUserPoolClient",
          "cognito-idp:GetUser",
          "cognito-idp:ListUsers",
        ]
        Resource = var.cognito_user_pool_arn != "" ? [var.cognito_user_pool_arn] : ["*"]
      }
    ]
  })

  tags = var.common_tags
}

# SSM read access — store future secrets (DB passwords, API keys) here
# instead of in the .env file
resource "aws_iam_policy" "ec2_ssm" {
  name        = "${var.project_name}-ec2-ssm-policy"
  description = "Allows EC2 to read SSM parameters under /${var.project_name}/"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SSMParameterRead"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
        ]
        Resource = "arn:aws:ssm:*:*:parameter/${var.project_name}/*"
      },
      {
        Sid      = "KMSDecrypt"
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = "*"
        Condition = {
          StringLike = {
            "kms:ViaService" = "ssm.*.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "ec2_cognito" {
  role       = aws_iam_role.ec2_app.name
  policy_arn = aws_iam_policy.ec2_cognito.arn
}

resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2_app.name
  policy_arn = aws_iam_policy.ec2_ssm.arn
}

# CloudWatch Logs — so Django/Nginx logs are visible in the console
resource "aws_iam_role_policy_attachment" "ec2_cloudwatch" {
  role       = aws_iam_role.ec2_app.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "ec2_app" {
  name = "${var.project_name}-ec2-app-profile"
  role = aws_iam_role.ec2_app.name

  tags = var.common_tags
}

# ── Admin IAM User ────────────────────────────────────────────────────────────
# Used for Terraform runs and initial deployment.
# After creating this user, generate access keys via the AWS console and
# store them in ~/.aws/credentials (never commit to git).

resource "aws_iam_user" "admin" {
  count = var.create_admin_user ? 1 : 0

  name = "${var.project_name}-admin"
  path = "/"

  tags = merge(var.common_tags, {
    Purpose = "Terraform and deployment admin"
  })
}

resource "aws_iam_user_policy_attachment" "admin_access" {
  count = var.create_admin_user ? 1 : 0

  user       = aws_iam_user.admin[0].name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
