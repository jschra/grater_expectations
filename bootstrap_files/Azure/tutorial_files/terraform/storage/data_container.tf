resource "azurerm_storage_container" "data_container" {
  name                  = var.data_container
  storage_account_name  = azurerm_storage_account.this.name
  container_access_type = "private"
}
