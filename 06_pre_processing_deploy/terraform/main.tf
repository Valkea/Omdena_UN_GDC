terraform {
  required_version = ">= 1.0"
  backend "local" {}  # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
  required_providers {
      aws = {
       source  = "hashicorp/aws"
       version = "~> 5.0"
      }
  }
}

# Collect environment variables
locals {
  environment_variables = { for tuple in regexall("(.*) = (.*)", file(".env")) : tuple[0] => sensitive(tuple[1]) }
}

# Configure the AWS Provider
provider "aws" {
  region = var.instance_region
}

################################################################################
# AWS Security Group
################################################################################

resource "aws_security_group" "sg" {
  name        = "deploy_lab_security"
  description = "Allow TLS inbound traffic"
  # vpc_id      = "my vpc id"

  ingress {
    description      = "TLS from VPC"
    from_port        = 0
    to_port          = 0
    protocol         = "all"
    cidr_blocks      = ["0.0.0.0/0"]
    # ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    # ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "allow_tls"
  }
}

################################################################################
# AWS EC2 Instance
################################################################################
# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/spot_instance_request
# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance

resource "aws_key_pair" "deployer" {
  key_name   = "terraform"
  # public_key = file("../output.pem.pub")
  public_key = file(var.ec2_pem_pub_file)
}

# Not compatible with the EC2 'stopped' initial state

resource "aws_eip" "ip-vps-env" {
  domain   = "vpc"
  instance = "${var.spot_instance == "true" ? "${aws_spot_instance_request.my_ec2_spot_instance[0].spot_instance_id}" : "${aws_instance.my_ec2_instance[0].id}"}"

}

resource "aws_spot_instance_request" "my_ec2_spot_instance" {
  ami           = var.instance_ami
  spot_price    = var.spot_price
  spot_type	= var.spot_type
  instance_type = var.instance_type
  count		= "${var.spot_instance == "true" ? 1 : 0}"
  associate_public_ip_address = "true" 
  vpc_security_group_ids      = [aws_security_group.sg.id]
  availability_zone = var.instance_availability_zone

  wait_for_fulfillment 	= "true"
  # block_duration_minutes	= 120

  tags = {
    Name = "MyEC2SpotInstance"
  }

  key_name  = aws_key_pair.deployer.id
  # user_data = file("../config_docker.sh")
  # user_data = file(var.ec2_config_file)
  # user_data = base64encode(templatefile(var.ec2_config_file, { docker_image = var.prepro_docker_image } ))
  user_data = base64encode(templatefile(var.ec2_config_file, { docker_image = "", docker_compose_path = var.prepro_docker_compose_path, PREFECT_API_KEY = local.environment_variables["PREFECT_API_KEY"], PREFECT_API_URL = local.environment_variables["PREFECT_API_URL"] } ))

  root_block_device {
    delete_on_termination = var.instance_ebs_delete_on_termination
    encrypted             = true
    volume_size           = var.instance_ebs_drive_size
  }
}

resource "aws_instance" "my_ec2_instance" {
  ami           = var.instance_ami
  instance_type = var.instance_type
  count		= "${var.spot_instance == "true" ? 0 : 1}"
  associate_public_ip_address = "true" 
  vpc_security_group_ids      = [aws_security_group.sg.id]
  availability_zone = var.instance_availability_zone
  
  tags = {
    Name = "MyEC2Instance"
  }

  key_name  = aws_key_pair.deployer.id
  # user_data = file("../config_docker.sh")
  # user_data = file(var.ec2_config_file)
  # user_data = base64encode(templatefile(var.ec2_config_file, { docker_image = var.prepro_docker_image } ))
  user_data = base64encode(templatefile(var.ec2_config_file, { docker_image = "", docker_compose_path = var.prepro_docker_compose_path, PREFECT_API_KEY = local.environment_variables["PREFECT_API_KEY"], PREFECT_API_URL = local.environment_variables["PREFECT_API_URL"] } ))

  root_block_device {
    delete_on_termination = var.instance_ebs_delete_on_termination
    encrypted             = true
    volume_size           = var.instance_ebs_drive_size
  }
}

# Define the initial state of the EC2 instance 

# resource "aws_ec2_instance_state" "my_ec2_state" {
#   instance_id = "${var.spot_instance == "true" ? "${aws_spot_instance_request.my_ec2_spot_instance[0].spot_instance_id}" : "${aws_instance.my_ec2_instance[0].id}"}"
#   state       = "stopped"
# }

# # Add extra space on the instance
# 
# resource "aws_ebs_volume" "volume" {
#   type = "gp3"
#   size = var.instance_ebs_drive_size
#   availability_zone = var.instance_availability_zone
# }
# 
# resource "aws_volume_attachment" "attachment" {
#   volume_id   = aws_ebs_volume.volume.id
#   instance_id = "${var.spot_instance == "true" ? "${aws_spot_instance_request.my_ec2_spot_instance[0].spot_instance_id}" : "${aws_instance.my_ec2_instance[0].id}"}"
#   device_name = "/dev/sda2"
# }

################################################################################
# AWS EventBridge Scheduler                                                        
################################################################################

# resource "aws_scheduler_schedule" "ec2-start-schedule" {
#   name = "ec2-start-schedule"
# 
#   flexible_time_window {
#     mode = "OFF"
#   }
# 
#   schedule_expression = var.scheduler_start_cron
#   schedule_expression_timezone = var.scheduler_cron_timezine
#   description = "Start instances event"
# 
#   target {
#     arn = "arn:aws:scheduler:::aws-sdk:ec2:startInstances"
#     role_arn = aws_iam_role.scheduler-ec2-role.arn
# 
#     input = jsonencode({
#       "InstanceIds": [
#   	"${var.spot_instance == "true" ? "${aws_spot_instance_request.my_ec2_spot_instance[0].spot_instance_id}" : "${aws_instance.my_ec2_instance[0].id}"}"
#       ]
#     })
#   }
# }
# 
# resource "aws_scheduler_schedule" "ec2-stop-schedule" {
#   name = "ec2-stop-schedule"
# 
#   flexible_time_window {
#     mode = "OFF"
#   }
# 
#   schedule_expression = var.scheduler_stop_cron
#   schedule_expression_timezone = var.scheduler_cron_timezine
#   description = "Stop instances event"
# 
#   target {
#     arn = "arn:aws:scheduler:::aws-sdk:ec2:stopInstances"
#     role_arn = aws_iam_role.scheduler-ec2-role.arn
# 
#     input = jsonencode({
#       "InstanceIds": [
#   	"${var.spot_instance == "true" ? "${aws_spot_instance_request.my_ec2_spot_instance[0].spot_instance_id}" : "${aws_instance.my_ec2_instance[0].id}"}"
#       ]
#     })
#   }
# }
# 
# locals {
#   shut_time = substr(tostring(timeadd(timestamp(), "5m")), 0, 19)
#   # shut_time = formatdate("YYYY-MM-DDThh:mm:ss", timeadd(timestamp(), "5m"))
#   shut_zone = formatdate("ZZZ", timestamp())
# }
# 
# resource "aws_scheduler_schedule" "ec2-stop-once-schedule" {
#   name = "ec2-stop-once-schedule"
# 
#   flexible_time_window {
#     mode = "OFF"
#   }
#  
#   schedule_expression = "at(${local.shut_time})"
#   schedule_expression_timezone = local.shut_zone
#   description = "Stop once instances event"
# 
#   target {
#     arn = "arn:aws:scheduler:::aws-sdk:ec2:stopInstances"
#     role_arn = aws_iam_role.scheduler-ec2-role.arn
# 
#     input = jsonencode({
#       "InstanceIds": [
#   	"${var.spot_instance == "true" ? "${aws_spot_instance_request.my_ec2_spot_instance[0].spot_instance_id}" : "${aws_instance.my_ec2_instance[0].id}"}"
#       ]
#     })
#   }
# }
# 
# resource "aws_iam_policy" "scheduler_ec2_policy" {
#   name = "scheduler_ec2_policy"
# 
#   policy = jsonencode(
#     {
#         "Version": "2012-10-17",
#         "Statement": [
#             {
#                 "Sid": "VisualEditor0",
#                 "Effect": "Allow",
#                 "Action": [
#                     "ec2:StartInstances",
#                     "ec2:StopInstances"
#                 ],
#                 "Resource": [
#   		    "*",
# 		    # "${aws_instance.my_ec2_instance[0].arn}:*",
# 		    # "${aws_instance.my_ec2_instance[0].arn}"
#                 ],
#             }
#         ]
#     }
#   )
# }
# 
# resource "aws_iam_role" "scheduler-ec2-role" {
#   name = "scheduler-ec2-role"
#   managed_policy_arns = [aws_iam_policy.scheduler_ec2_policy.arn]
# 
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Sid    = ""
#         Principal = {
#           Service = "scheduler.amazonaws.com"
#         }
#       },
#     ]
#   })
# }


################################################################################
# AWS S3 Bucket
################################################################################
# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket

resource "aws_s3_bucket" "gdc_bucket" {
  bucket 	= "omdena-un-gdc-bucket-02"
  force_destroy = var.s3_force_destroy
  count 	= "${var.s3_instance == "true" ? 1 : 0}"

  tags = {
    Name        = var.s3_name
    Environment = "Dev"
  }
}
