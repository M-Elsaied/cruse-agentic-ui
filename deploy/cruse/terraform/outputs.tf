output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.cruse.id
}

output "elastic_ip" {
  description = "Public Elastic IP address"
  value       = aws_eip.cruse.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i <key>.pem ubuntu@${aws_eip.cruse.public_ip}"
}

output "app_url" {
  description = "URL to access the CRUSE application"
  value       = "http://${aws_eip.cruse.public_ip}"
}
