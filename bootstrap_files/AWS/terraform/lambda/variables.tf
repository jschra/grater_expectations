variable "image_uri" {
  type        = string
  description = "URI for the Docker image to deploy as lambda"
}

variable "ge-bucket-name" {
  type        = string
  description = "Name for bucket to be used to store GE outputs"
}

variable "ge-site-bucket-name" {
  type        = string
  description = "Name for bucket to be used to generate the GE site in"
}

variable "ge-data-bucket-name" {
  type        = string
  description = "Name for bucket to be used to store tutorial data"
}
