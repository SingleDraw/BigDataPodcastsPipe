# First, add your blob storage connection string to Key Vault
resource "azurerm_key_vault_secret" "blob_connection_string" {
  name         = "blob-storage-connection-string"
  value        = azurerm_storage_account.storage.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}

# Method 1: Azure Container Instances with Key Vault integration
resource "azurerm_container_group" "app" {
  name                = "my-app"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  
  # Identity for Key Vault access
  identity {
    type = "SystemAssigned"
  }

  container {
    name   = "app"
    image  = "${azurerm_container_registry.acr.login_server}/myapp:latest"
    cpu    = "0.5"
    memory = "1.5"

    ports {
      port     = 80
      protocol = "TCP"
    }

    # Environment variables from Key Vault
    environment_variables = {
      "KEY_VAULT_URL" = azurerm_key_vault.kv.vault_uri
    }

    # Secure environment variables (optional alternative)
    secure_environment_variables = {
      # You can reference secrets directly if using data sources
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.acr.login_server
    username = azurerm_container_registry.acr.admin_username
    password = azurerm_container_registry.acr.admin_password
  }
}

# Grant the container group access to Key Vault
resource "azurerm_key_vault_access_policy" "container_policy" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_container_group.app.identity[0].principal_id

  secret_permissions = [
    "Get",
    "List"
  ]
}

# Method 2: Azure Container Apps (recommended for production)
resource "azurerm_container_app_environment" "app_env" {
  name                       = "my-app-env"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id
}

resource "azurerm_container_app" "app" {
  name                         = "my-app"
  container_app_environment_id = azurerm_container_app_environment.app_env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    username = azurerm_container_registry.acr.admin_username
    password = azurerm_container_registry.acr.admin_password
  }

  secret {
    name  = "blob-connection-string"
    value = azurerm_storage_account.storage.primary_connection_string
    # Alternative: reference from Key Vault using identity
  }

  template {
    container {
      name   = "app"
      image  = "${azurerm_container_registry.acr.login_server}/myapp:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "BLOB_CONNECTION_STRING"
        secret_name = "blob-connection-string"
      }

      env {
        name  = "KEY_VAULT_URL"
        value = azurerm_key_vault.kv.vault_uri
      }
    }
  }
}

# Method 3: Using data sources to retrieve secrets (for other resources)
data "azurerm_key_vault_secret" "blob_connection" {
  name         = "blob-storage-connection-string"
  key_vault_id = azurerm_key_vault.kv.id
  
  # This requires the Terraform service principal to have access
  depends_on = [azurerm_key_vault_secret.blob_connection_string]
}

# Example: Using the secret in an App Service
resource "azurerm_linux_web_app" "webapp" {
  name                = "my-webapp"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.asp.id

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    "BLOB_CONNECTION_STRING" = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.kv.name};SecretName=blob-storage-connection-string)"
    "DOCKER_REGISTRY_SERVER_URL"      = "https://${azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME" = azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD" = azurerm_container_registry.acr.admin_password
  }

  site_config {
    application_stack {
      docker_image     = "${azurerm_container_registry.acr.login_server}/myapp"
      docker_image_tag = "latest"
    }
  }
}

# Grant App Service access to Key Vault
resource "azurerm_key_vault_access_policy" "webapp_policy" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_web_app.webapp.identity[0].principal_id

  secret_permissions = [
    "Get"
  ]
}