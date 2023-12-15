variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "instance_ami" {
  type = string
  default = "ami-0694d931cee176e7d" # Ubuntu Server 22.04 LTS (64-bit (x86))
  description = "Instance AMI image to use, by default Ubuntu 22.04 LTS"
}

variable "spot_instance" {
  type = string
  default = "true"
  description = "This value is true if we want to use a spot instance instead of a regular one"
}

variable "spot_price" {
  type = string
  default = "0.0060"
  description = "Maximum price to pay for spot instance"
}

variable "spot_type" {
  type = string
  default = "one-time"
  description = "Spot instance type, this value only applies for spot instance type."
}

variable "s3_instance" {
  type = string
  default = "false"
  description = "This value is true if we want to use an S3 instance"
}

# locals {
#   gdc-bucket = "omdena-un-gdc-bucket"
# }
# 
# variable "storage_class" {
#   description = "Storage class type for your bucket. Check official docs for more info."
#   default = "STANDARD"
# }
