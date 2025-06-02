# 1. RESOURCE GROUP
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# 2. STORAGE ACCOUNT
resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"  
  public_network_access_enabled   = true                                        # for access from remote machines outside azure
  allow_nested_items_to_be_public = false
  is_hns_enabled           = true                                               # Enables Data Lake Gen2 (ABFS)
}

# 3. STORAGE CONTAINER FOR TERRAFORM STATE
resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# 4. CONTAINER REGISTRY SECRET
resource "azurerm_key_vault_secret" "blob_connection_string" {
  name         = "blob-storage-connection-string"
  value        = azurerm_storage_account.storage.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}

## 5. Automatically set GitHub secrets
resource "github_actions_secret" "resource_group_name" {
  repository      = var.github_repository
  secret_name     = "AZURE_RESOURCE_GROUP"
  plaintext_value = azurerm_resource_group.rg.name
}

resource "github_actions_secret" "storage_account_name" {
  repository      = var.github_repository
  secret_name     = "STORAGE_ACCOUNT_NAME"
  plaintext_value = azurerm_storage_account.storage.name
}

data "azurerm_client_config" "current" {}

