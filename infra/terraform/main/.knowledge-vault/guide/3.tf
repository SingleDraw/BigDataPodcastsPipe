# First, you need to retrieve secrets from Key Vault using data sources
data "azurerm_key_vault_secret" "blob_connection" {
  name         = "blob-storage-connection-string"  # The secret name you created
  key_vault_id = azurerm_key_vault.kv.id
}

data "azurerm_key_vault_secret" "database_password" {
  name         = "db-password"
  key_vault_id = azurerm_key_vault.kv.id
}

# Now you can use these in container secure environment variables
resource "azurerm_container_group" "app" {
  name                = "my-app"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"

  container {
    name   = "app"
    image  = "myapp:latest"
    cpu    = "0.5"
    memory = "1.5"

    # REGULAR environment variables (visible in Azure portal)
    environment_variables = {
      "APP_ENV"     = "production"
      "LOG_LEVEL"   = "info"
      "SERVER_PORT" = "8080"
    }

    # SECURE environment variables (encrypted, not visible in portal)
    secure_environment_variables = {
      "DATABASE_PASSWORD"    = data.azurerm_key_vault_secret.database_password.value
      "BLOB_CONNECTION_STR" = data.azurerm_key_vault_secret.blob_connection.value
      "API_SECRET_KEY"      = "hardcoded-secret-here"  # You can also hardcode if needed
    }
  }
}

# IMPORTANT: For the data sources to work, your Terraform service principal 
# needs access to the Key Vault
resource "azurerm_key_vault_access_policy" "terraform_policy" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id  # Your Terraform SP

  secret_permissions = [
    "Get", "List"  # Terraform needs these to read secrets
  ]
}

# ALTERNATIVE: If you don't want to use data sources, you can reference directly
resource "azurerm_container_group" "app_alternative" {
  name                = "my-app-alt"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"

  container {
    name   = "app"
    image  = "myapp:latest"
    cpu    = "0.5"
    memory = "1.5"

    # Direct reference to storage account (not from Key Vault)
    secure_environment_variables = {
      "BLOB_CONNECTION_STR" = azurerm_storage_account.storage.primary_connection_string
    }
  }
}