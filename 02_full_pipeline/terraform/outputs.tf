# Not compatible with the EC2 'stopped' initial state
#
# output "ubuntu_ip" {
#   value = aws_eip.ip-vps-env.public_ip
#   description = "Instance IP"
#   depends_on = [
# 	aws_spot_instance_request.my_ec2_spot_instance, 
# 	aws_instance.my_ec2_instance
#   ]
# }
# output "ubuntu_dns" {
#   value = aws_eip.ip-vps-env.public_dns
#   description = "Instance DNS"
#   depends_on = [
# 	aws_spot_instance_request.my_ec2_spot_instance, 
# 	aws_instance.my_ec2_instance
#   ]
# }
# output "Flask_URL" {
#   value = "http://${aws_eip.ip-vps-env.public_dns}:5000"
#   description = "Instance DNS"
#   depends_on = [
# 	aws_spot_instance_request.my_ec2_spot_instance, 
# 	aws_instance.my_ec2_instance
#   ]
# }
