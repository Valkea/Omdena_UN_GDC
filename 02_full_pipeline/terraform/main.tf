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

# Configure the AWS Provider
provider "aws" {
  region = "eu-west-1"
}

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
  public_key = file("../output.pem.pub")
}

resource "aws_eip" "ip-vps-env" {
  instance = "${var.spot_instance == "true" ? "${aws_spot_instance_request.my_ec2_spot_instance[0].spot_instance_id}" : "${aws_instance.my_ec2_instance[0].id}"}"

  domain      = "vpc"
  depends_on = [
	aws_spot_instance_request.my_ec2_spot_instance, 
	aws_instance.my_ec2_instance
  ]
}

resource "aws_spot_instance_request" "my_ec2_spot_instance" {
  ami           = var.instance_ami
  spot_price    = var.spot_price
  spot_type	= var.spot_type
  instance_type = var.instance_type
  count		= "${var.spot_instance == "true" ? 1 : 0}"
  associate_public_ip_address = "true" 
  vpc_security_group_ids      = [aws_security_group.sg.id]

  wait_for_fulfillment 	= "true"
  # block_duration_minutes	= 120

  tags = {
    Name = "MyEC2SpotInstance"
  }

  key_name  = aws_key_pair.deployer.id
  user_data = file("../config_docker.sh")
#
#  provisioner "file" {
#    source      = "../config_docker.sh"
#    destination = "/tmp/script.sh"
#  
#    connection {
#      type     = "ssh"
#      user     = "ubuntu"
#      private_key = file("../output.pem")
#      host = self.public_ip
#    }
#  }

}

resource "aws_instance" "my_ec2_instance" {
  ami           = var.instance_ami
  instance_type = var.instance_type
  count		= "${var.spot_instance == "true" ? 0 : 1}"
  associate_public_ip_address = "true" 
  vpc_security_group_ids      = [aws_security_group.sg.id]

  tags = {
    Name = "MyEC2Instance"
  }

  key_name  = aws_key_pair.deployer.id
  user_data = file("../config_docker.sh")

#   provisioner "file" {
#     source      = "../config_docker.sh"
#     destination = "/tmp/script.sh"
#   
#     connection {
#       type     = "ssh"
#       user     = "ubuntu"
#       private_key = file("../output.pem")
#       host = self.public_ip
#     }
#   }
}

################################################################################
# AWS S3 Bucket
################################################################################
# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket

resource "aws_s3_bucket" "gdc_bucket" {
  bucket 	= "omdena-un-gdc-bucket-02"
  force_destroy = true
  count 	= "${var.s3_instance == "true" ? 1 : 0}"

  tags = {
    Name        = "omdena-un-gdc-bucket-02"
    Environment = "Dev"
  }
}
