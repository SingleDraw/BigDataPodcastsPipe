
# 9. Azure Container Instance
# -----------------------------------------------------------------
# This section sets up an Azure Container Instance to run big data ephemeral jobs
# It uses the user-assigned identity to access storage and key vault
resource "azurerm_container_group" "ephemeral_job" {
  name                = "${var.resource_group_name}-aci-job"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  restart_policy      = "Never" # Run once and exit

  identity {
    type              = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.storage_identity.id,
      # azurerm_user_assigned_identity.key_vault_identity.id
    ]
    # identity_ids = [azurerm_user_assigned_identity.aci_identity.id] # Single identity for both storage and key vault
  }
  container {
    name   = "brick-pcaster"
    image  = "${azurerm_container_registry.acr.login_server}/${var.brick_pcaster_image_name}:latest"
    cpu    = "1.0"
    memory = "1.5"

    command = [
      "pcaster",
      "--overwrite",
      "--azure-storage-account", azurerm_storage_account.storage.name
    ]

    environment_variables = {
      "AZURE_STORAGE_ACCOUNT"      = azurerm_storage_account.storage.name
      # "STORAGE_ACCOUNT_KEY"        = azurerm_storage_account.storage.primary_access_key
      # "KEY_VAULT_URI"              = azurerm_key_vault.kv.vault_uri
      # "PODCAST_API_KEY"            = azurerm_key_vault_secret.podcast_api_key.value
      # "PODCAST_API_SECRET"         = azurerm_key_vault_secret.podcast_api_secret.value
    }

    secure_environment_variables = {}

    # ports {
    #   port     = 80
    #   protocol = "TCP"
    # }

  }

  image_registry_credential {
    server   = azurerm_container_registry.acr.login_server
    username = azurerm_container_registry.acr.admin_username
    password = azurerm_container_registry.acr.admin_password
  }

  # Optional: Add diagnostics settings for logging
  # diagnostics {
  #   log_analytics_workspace_id = azurerm_log_analytics_workspace.log.id
  # }

  diagnostics {
    log_analytics {
      workspace_id  = azurerm_log_analytics_workspace.law.id
      workspace_key = azurerm_log_analytics_workspace.law.primary_shared_key
    }
  }

  # timeout_in_seconds = 180  # 3 minutes timeout
}