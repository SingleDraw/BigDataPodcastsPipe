# 1. Read existing storage account
data "azurerm_storage_account" "storage" {
  name                = var.storage_account_name
  resource_group_name = var.resource_group_name
}

# 3. CONTAINER REGISTRY
resource "azurerm_container_registry" "acr" {
  name                = var.container_registry_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"                                                 # cheapers option
  admin_enabled       = true                                                    # Enables username/password access
}

# 4. KEY VAULT
resource "azurerm_key_vault" "kv" {
  name                = "${var.resource_group_name}-kv"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    secret_permissions = [
      "Get", "List", "Set", "Delete"
    ]
  }
}

# 5. Store secrets in Key Vault
resource "azurerm_key_vault_secret" "acr_username" {
  name         = "acr-admin-username"
  value        = azurerm_container_registry.acr.admin_username
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "acr_password" {
  name         = "acr-admin-password"
  value        = azurerm_container_registry.acr.admin_password
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "blob_connection_string" {
  name         = "blob-storage-connection-string"
  value        = azurerm_storage_account.storage.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}

## 6. Automatically set GitHub secrets

# A. Container Registry Login Server
resource "github_actions_secret" "acr_login_server" {
  repository      = var.github_repository
  secret_name     = "ACR_LOGIN_SERVER"
  plaintext_value = azurerm_container_registry.acr.login_server
}

# B. Key Vault Credentials
resource "github_actions_secret" "acr_username" {
  repository = var.github_repository
  secret_name = "ACR_USERNAME"
  plaintext_value = azurerm_key_vault_secret.acr_username.value
}

resource "github_actions_secret" "acr_password" {
  repository = var.github_repository
  secret_name = "ACR_PASSWORD"
  plaintext_value = azurerm_key_vault_secret.acr_password.value
}

# C. Resources names
resource "github_actions_secret" "key_vault_name" {
  repository      = var.github_repository
  secret_name     = "KEY_VAULT_NAME"
  plaintext_value = azurerm_key_vault.kv.name
}

data "azurerm_client_config" "current" {}

