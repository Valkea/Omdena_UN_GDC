# Not compatible with the EC2 'stopped' initial state

output "ubuntu_ip" {
  value = aws_eip.ip-vps-env.public_ip
  description = "Instance IP"
}

output "ubuntu_dns" {
  value = aws_eip.ip-vps-env.public_dns
  description = "Instance DNS"
}

output "Flask_PUBLIC_DNS" {
  value = "http://${aws_eip.ip-vps-env.public_ip}:5000"
  description = "Instance IP"
}

output "Flask_PUBLIC_URL" {
  value = "http://${aws_eip.ip-vps-env.public_dns}:5000"
  description = "Instance DNS"
}
