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
  default = "persistent"
# default = "one-time"
  description = "Spot instance type, this value only applies for spot instance type."
}

variable "s3_instance" {
  type = string
  default = "false"
  description = "This value is true if we want to use an S3 instance"
}

variable "scheduler_start_cron" {
  type = string
  default = "cron(0,15,30,45 * ? * MON-FRI *)"
  description = "The (AWS) cron expession for stopping the EC2 instance for the data-collection & indexing"
}

variable "scheduler_stop_cron" {
  type = string
  default = "cron(5,20,35,50 * ? * MON-FRI *)"
  description = "The (AWS) cron expession for starting the EC2 instance for the data-collection & indexing"
}

variable "scheduler_cron_timezine" {
  type = string
  default = "UTC"
  description = "The timezone for the start and stop cron expressions"
}

# locals {
#   gdc-bucket = "omdena-un-gdc-bucket"
# }
# 
# variable "storage_class" {
#   description = "Storage class type for your bucket. Check official docs for more info."
#   default = "STANDARD"
# }
