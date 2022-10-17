variable "resource_group_name" {
  description = "Name of the resource group to provision and to deploy resources in"
  type        = string
}

variable "storage_account_name" {
  description = "Name of the storage account to deploy"
  type        = string
}

variable "app_service_name" {
  description = "Name for the service app plan to be deployed"
  type        = string
}

variable "function_name" {
  description = "Name of the linux function to be deployed"
  type        = string
}

variable "docker_image_name" {
  description = "Name of the docker image to be deployed as Azure Function"
  type        = string
}

variable "container_registry_name" {
  description = "Name of the Azure Container registry where the docker image of the Azure Function is stored"
  type        = string
}
