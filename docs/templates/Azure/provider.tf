# NOTE: It's best to run Terraform using state stored in a state bucket. For more
# information, please refer to https://www.terraform.io/language/state/remote
{% raw %}

# We strongly recommend using the required_providers block to set the
# Azure Provider source and version being used
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.0.0"
    }
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {}
}

{% endraw %}