# 1. Create Storage Account (you probably already have this)
resource "azurerm_storage_account" "storage" {
  name                     = "mystorageaccount123"  # Must be globally unique
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# 2. NO OUTPUT NEEDED - Terraform automatically knows the connection string
# The storage account resource has built-in attributes you can reference directly:
# - azurerm_storage_account.storage.primary_connection_string
# - azurerm_storage_account.storage.secondary_connection_string
# - azurerm_storage_account.storage.name
# - azurerm_storage_account.storage.primary_access_key

# 3. Store the connection string in Key Vault
resource "azurerm_key_vault_secret" "blob_connection_string" {
  name         = "blob-storage-connection-string"  # This is YOUR chosen secret name
  value        = azurerm_storage_account.storage.primary_connection_string  # Direct reference
  key_vault_id = azurerm_key_vault.kv.id  # Reference to your Key Vault resource
  
  # This depends_on ensures storage account is created first
  depends_on = [azurerm_storage_account.storage]
}

# 4. You can store multiple secrets with different names
resource "azurerm_key_vault_secret" "storage_account_name" {
  name         = "storage-account-name"
  value        = azurerm_storage_account.storage.name
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "storage_access_key" {
  name         = "storage-access-key"
  value        = azurerm_storage_account.storage.primary_access_key
  key_vault_id = azurerm_key_vault.kv.id
}