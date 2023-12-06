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

# Data Lake Bucket
# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket
resource "aws_s3_bucket" "gdc_bucket" {
  bucket = "omdena-un-gdc-bucket"
  force_destroy = true

  tags = {
    Name        = "omdena-un-gdc-bucket"
    Environment = "Dev"
  }
}

# Bucket Public Access
# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block
resource "aws_s3_bucket_public_access_block" "gdc_bucket" {
  bucket = aws_s3_bucket.gdc_bucket.id

  block_public_acls       = false 
  block_public_policy     = false 
  ignore_public_acls      = false 
  restrict_public_buckets = false 
}
