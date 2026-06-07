# Module: networking

Creates the AWS network foundation for Mitumba Shop Manager.

## Resources created

| Resource | Description |
|---|---|
| `aws_vpc` | Isolated network with DNS support |
| `aws_internet_gateway` | Outbound internet access for the public subnet |
| `aws_subnet` (public) | Single AZ public subnet; instances get a public IP |
| `aws_route_table` | Default route → IGW |
| `aws_security_group` | Ports 22 (SSH), 80 (HTTP), 443 (HTTPS) |

## Usage

```hcl
module "networking" {
  source = "../../modules/networking"

  project_name       = "mitumba"
  aws_region         = "us-east-1"
  vpc_cidr           = "10.0.0.0/16"
  public_subnet_cidr = "10.0.1.0/24"
  ssh_allowed_cidrs  = ["YOUR_IP/32"]   # restrict SSH to your IP

  common_tags = {
    Project     = "mitumba"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

## Migrating to a different AWS account

No code changes are required. Update `terraform.tfvars` (or the calling
environment variables) with the new region, CIDR ranges, and tags.  Run
`terraform init` to refresh provider credentials and `terraform plan` to
review before applying.

## Inputs

| Name | Description | Default |
|---|---|---|
| `project_name` | Prefix for all resource names | — |
| `aws_region` | AWS region (subnet is placed in `{region}a`) | — |
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` |
| `public_subnet_cidr` | Public subnet CIDR | `10.0.1.0/24` |
| `ssh_allowed_cidrs` | CIDRs allowed to SSH | `["0.0.0.0/0"]` |
| `common_tags` | Tags applied to all resources | `{}` |

## Outputs

| Name | Description |
|---|---|
| `vpc_id` | VPC ID |
| `public_subnet_id` | Subnet ID for the EC2 instance |
| `web_security_group_id` | Security group ID attached to EC2 |
