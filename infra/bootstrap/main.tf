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
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
}

# 4. Create a storage container for Whisperer files
resource "azurerm_storage_container" "whisperer" {
  name                  = "whisperer"
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
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

# Register the Microsoft.App provider for Container Apps
resource "null_resource" "register_containerapps" {
  provisioner "local-exec" {
    command = "az provider register -n Microsoft.App --wait"
  }

  triggers = {
    # always_run = timestamp()  # Ensures this runs every time you apply
    rg_name = azurerm_resource_group.rg.name # This ensures it runs after the resource group is created
  }
}

data "azurerm_client_config" "current" {}

