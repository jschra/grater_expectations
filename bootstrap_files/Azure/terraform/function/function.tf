# -------------------------------------------------------------
# App service plan
# ------------------------------------------------------------- 
resource "azurerm_service_plan" "this" {
  name                = var.app_service_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  os_type             = "Linux"
  sku_name            = "B1"
}

data "azurerm_container_registry" "this" {
  name                = "gratertutorialregistry"
  resource_group_name = azurerm_resource_group.this.name
}

resource "azurerm_storage_account" "function" {
  name                     = "testfordockerimage"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  tags = {
    description = "Storage for function app"
  }
}
# -------------------------------------------------------------
# Azure function
# ------------------------------------------------------------- 
resource "azurerm_linux_function_app" "this" {
  name                = var.function_name
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name

  storage_account_name       = azurerm_storage_account.function.name
  storage_account_access_key = azurerm_storage_account.function.primary_access_key
  service_plan_id            = azurerm_service_plan.this.id

  app_settings = {
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = false
  }

  site_config {
    # always_on = true
    #linux_fx_version = "DOCKER|gratertutorialregistry.azurecr.io/test_docker_image:latest"
    application_stack {
      docker {
        registry_url      = data.azurerm_container_registry.this.login_server
        image_name        = "test_docker_image"
        image_tag         = "latest"
        registry_username = data.azurerm_container_registry.this.admin_username
        registry_password = data.azurerm_container_registry.this.admin_password
      }
    }
  }
}