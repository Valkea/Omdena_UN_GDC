# Not compatible with the EC2 'stopped' initial state

output "ubuntu_ip" {
  value = aws_eip.ip-vps-env.public_ip
  description = "Instance IP"
}

output "ubuntu_dns" {
  value = aws_eip.ip-vps-env.public_dns
  description = "Instance DNS"
}

output "Weaviate_PUBLIC_DNS" {
  value = "http://${aws_eip.ip-vps-env.public_ip}:8080"
  description = "Instance IP"
}

output "Weaviate_PUBLIC_URL" {
  value = "http://${aws_eip.ip-vps-env.public_dns}:8080"
  description = "Instance DNS"
}

# output "envs" {
#   value = local.environment_variables
#   sensitive = true # this is required if the sensitive function was used when loading .env file (more secure way)
# }
# 
# output "envs2" {
#   value = local.environment_variables["PREFECT_API_URL"]
#   sensitive = true # this is required if the sensitive function was used when loading .env file (more secure way)
# }
