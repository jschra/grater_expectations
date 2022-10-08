variable "region" {
  description = "Region wherein Azure services should be deployed"
  type        = string
  default     = "West Europe"
}

variable "resource_group_name" {
  description = "Name of the resource group to provision and to deploy resources in"
  type        = string
}

variable "storage_account_name" {
  description = "Name of the storage account to deploy"
  type        = string
}

variable "ge_artifact_container" {
  description = "Name of the container to spin up for publishing Great Expectations artifacts to"
  type        = string
  default     = "ge-artifacts"
}
