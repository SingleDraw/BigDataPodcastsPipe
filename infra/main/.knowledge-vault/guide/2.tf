# Your Key Vault resource (from your original code)
resource "azurerm_key_vault" "kv" {  # "kv" is YOUR chosen resource name in Terraform
  name                = "${var.resource_group_name}-kv"  # Actual Azure resource name
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

# EXPLANATION:
# - "kv" = YOUR chosen Terraform resource name (you could call it "my_vault", "main_kv", etc.)
# - azurerm_key_vault.kv.id = Terraform automatically creates this attribute
# - It's NOT hardcoded - it's a dynamic reference to your Key Vault's Azure resource ID

# SECRET NAMES - You choose these names:
resource "azurerm_key_vault_secret" "database_password" {
  name         = "db-password"              # YOUR chosen secret name in Key Vault
  value        = "super-secret-password"    # The actual secret value
  key_vault_id = azurerm_key_vault.kv.id   # Reference to YOUR Key Vault
}

resource "azurerm_key_vault_secret" "api_key" {
  name         = "external-api-key"         # Another secret name YOU choose
  value        = "abc123xyz789"
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "connection_strings" {
  name         = "redis-connection"         # Yet another name YOU choose
  value        = "redis://localhost:6379"
  key_vault_id = azurerm_key_vault.kv.id
}

# Common naming patterns for secrets:
# - "database-connection-string"
# - "api-key-external-service"
# - "smtp-password"
# - "jwt-secret"
# - "storage-account-key"