##############################################################################
# networking/outputs.tf
# Values consumed by the compute and other modules.
##############################################################################

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the public subnet where EC2 is launched"
  value       = aws_subnet.public.id
}

output "web_security_group_id" {
  description = "ID of the security group attached to the EC2 instance"
  value       = aws_security_group.web.id
}
