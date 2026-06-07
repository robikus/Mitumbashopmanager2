##############################################################################
# compute/outputs.tf
##############################################################################

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "Elastic IP assigned to the instance — point your DNS A record here"
  value       = aws_eip.app.public_ip
}

output "public_dns" {
  description = "Public DNS name of the Elastic IP"
  value       = aws_eip.app.public_dns
}

output "ami_id" {
  description = "AMI used to launch the instance (Ubuntu 22.04 LTS)"
  value       = data.aws_ami.ubuntu.id
}
