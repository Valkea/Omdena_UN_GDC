locals {
  gdc-bucket = "omdena-un-gdc-bucket"
}

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}
