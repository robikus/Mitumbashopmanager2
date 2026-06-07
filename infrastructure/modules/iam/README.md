# Module: iam

Creates the IAM identities required by Mitumba Shop Manager.

## Resources

### EC2 App Role (`<project>-ec2-app-role`)

Attached to the EC2 instance via an Instance Profile.  Grants least-privilege
access to:

| Permission | Why |
|---|---|
| `cognito-idp:DescribeUserPool*` | Allows the app to look up pool configuration at startup |
| `ssm:GetParameter*` | Lets the app read secrets from Parameter Store (DB password, keys) |
| `CloudWatchAgentServerPolicy` | Ships logs to CloudWatch Logs |

The instance never needs hard-coded AWS credentials — it uses the role.

### Admin IAM User (`<project>-admin`)

Created only when `create_admin_user = true` (default).  Has
`AdministratorAccess` — intended for the engineer running Terraform and
first-deploy scripts.

After `terraform apply`:

1. Go to **IAM → Users → `<project>-admin` → Security credentials**
2. Create an access key
3. Store it in `~/.aws/credentials` (never commit)
4. Optionally enable MFA

## Inputs

| Name | Default | Description |
|---|---|---|
| `project_name` | — | Resource name prefix |
| `cognito_user_pool_arn` | `""` | Scopes Cognito policy to this pool (`"*"` if empty) |
| `create_admin_user` | `true` | Whether to create the admin IAM user |

## Outputs

| Name | Description |
|---|---|
| `ec2_instance_profile_name` | Passed to compute module |
| `ec2_role_arn` | Role ARN |
| `admin_user_name` | Admin user name (empty if not created) |

## Migrating to a different AWS account

No code changes required.  Resource names are prefixed with `project_name`.
The admin user's access keys must be regenerated in the new account after
`terraform apply`.
