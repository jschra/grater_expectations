# -------------------------------------------------------------
# Storage account
# ------------------------------------------------------------- 

resource "azurerm_storage_account" "this" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  static_website {
    index_document = "index.html"
  }

  tags = {
    description = "Grater Expectations storage account"
  }
}

# -------------------------------------------------------------
# Containers
# ------------------------------------------------------------- 

resource "azurerm_storage_container" "ge_artifacts" {
  name                  = var.ge_artifact_container
  storage_account_name  = azurerm_storage_account.this.name
  container_access_type = "private"
}
