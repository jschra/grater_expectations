variable "resource_group_name" {
  description = "Name of the resource group to provision and to deploy resources in"
  type        = string
  default     = "Grater-Expectations-tutorial"
}

variable "storage_account_name" {
  description = "Name of the storage account to deploy"
  type        = string
  default     = "joriktestterraform"
}

variable "app_service_name" {
  description = "Name for the service app plan to be deployed"
  type        = string
  default     = "grater-expectations-service-plan"
}

variable "function_name" {
  description = "Name of the linux function to be deployed"
  type        = string
  default     = "grater-expectations-function"
}
