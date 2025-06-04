
# Long-lived Azure resources for Big Data Pipelines
# This Terraform script sets up the necessary Azure resources for a Big Data pipeline

# 1. Azure Resource Group
# -----------------------------------------------------------------
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# 2. Azure Storage Account
# -----------------------------------------------------------------
resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"  
  public_network_access_enabled   = true  # for remote access
  allow_nested_items_to_be_public = false
  is_hns_enabled           = true # Enables Data Lake Gen2 (ABFS)
}

# 3. ACR - Azure Container Registry
# -----------------------------------------------------------------
resource "azurerm_container_registry" "acr" {
  name                = var.container_registry_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"   # economical tier
  admin_enabled       = true      # Enables username/password access
}

# 4. KV - Azure Key Vault
# -----------------------------------------------------------------
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
# Store GitHub secrets in Key Vault
#--------------------------------------------------------------

# Podcasting Index Api Secrets
resource "azurerm_key_vault_secret" "podcast_api_key" {
  name         = "PodcastingIndexApiKey"
  value        = var.podcasting_index_api_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "podcast_api_secret" {
  name         = "PodcastingIndexApiSecret"
  value        = var.podcasting_index_api_secret
  key_vault_id = azurerm_key_vault.main.id
}

# Store ACR credentials in Key Vault
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

# Store storage connection string
resource "azurerm_key_vault_secret" "blob_connection_string" {
  name         = "blob-storage-connection-string"
  value        = azurerm_storage_account.storage.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}



#-------------------------------------------------------------
# 7. User-Assigned Managed Identity - Storage Account
# -----------------------------------------------------------------
# This identity will be used for read and write to storage account
# -----------------------------------------------------------------

resource "azurerm_user_assigned_identity" "storage_identity" {
  name                = "${var.resource_group_name}-storage-identity"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
}

# This role assignment allows the identity to read/write to the storage account
resource "azurerm_role_assignment" "storage_identity_role" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.storage_identity.principal_id
}

#-------------------------------------------------------------
# 8. User-Assigned Managed Identity - Key Vault
# -----------------------------------------------------------------
# This identity will be used for accessing Key Vault secrets
# -----------------------------------------------------------------
resource "azurerm_user_assigned_identity" "key_vault_identity" {
  name                = "${var.resource_group_name}-key-vault-identity"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
}

# This role assignment allows the identity to access Key Vault secrets
resource "azurerm_role_assignment" "key_vault_identity_role" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.key_vault_identity.principal_id
}

# 9. User-assigned identity (for ACI to use)
# -----------------------------------------------------------------
# This identity will be used by ephemeral Azure Container Instances (ACI) 
# to pull images from ACR and access storage
# Role assignments:
#   ACI identity → Storage Blob Data Contributor on your Storage Account
#   ACI identity → Reader + AcrPull on ACR.

resource "azurerm_user_assigned_identity" "aci_identity" {
  name                = "${var.resource_group_name}-aci-identity"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
}
resource "azurerm_role_assignment" "aci_identity_role" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aci_identity.principal_id
}
resource "azurerm_role_assignment" "aci_storage_role" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.aci_identity.principal_id
}



# 6. Automatically set GitHub secrets
# This section sets GitHub secrets automatically using the GitHub Actions Secrets API
# Ensure you have the GitHub Actions provider configured in your Terraform setup
#-------------------------------------------------------------

# Aci Identity Resource ID
resource "github_actions_secret" "aci_identity_id" {
  repository      = var.github_repository
  secret_name     = "IDENTITY_RESOURCE_ID"
  plaintext_value = azurerm_user_assigned_identity.aci_identity.id
}

# Container Registry Login Server
resource "github_actions_secret" "acr_login_server" {
  repository      = var.github_repository
  secret_name     = "ACR_LOGIN_SERVER"
  plaintext_value = azurerm_container_registry.acr.login_server
}

# Key Vault Credentials
resource "github_actions_secret" "acr_username" {
  repository      = var.github_repository
  secret_name     = "ACR_USERNAME"
  plaintext_value = azurerm_key_vault_secret.acr_username.value
}

resource "github_actions_secret" "acr_password" {
  repository      = var.github_repository
  secret_name     = "ACR_PASSWORD"
  plaintext_value = azurerm_key_vault_secret.acr_password.value
}

# Resources names
resource "github_actions_secret" "key_vault_name" {
  repository      = var.github_repository
  secret_name     = "KEY_VAULT_NAME"
  plaintext_value = azurerm_key_vault.kv.name
}

data "azurerm_client_config" "current" {}

#-------------------------------------------------------------
# 10. Azure Data Factory - Big Data Pipeline Runner
# -----------------------------------------------------------------
# This section sets up Azure Data Factory to run big data pipelines
resource "azurerm_data_factory" "adf" {
  name                = "${var.resource_group_name}-adf"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.storage_identity.id,
      azurerm_user_assigned_identity.key_vault_identity.id
    ]
  }
}

resource "github_actions_secret" "adf_name" {
  repository      = var.github_repository
  secret_name     = "ADF_NAME"
  plaintext_value = azurerm_data_factory.adf.name
}

# or
resource "azurerm_role_assignment" "adf_contributor" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_data_factory.adf.identity[0].principal_id
}

# resource "azurerm_data_factory_pipeline" "pipeline" {
#   name                = "big-data-pipeline"
#   data_factory_id     = azurerm_data_factory.adf.id
#   description         = "Pipeline to run big data jobs"
  
#   # Define activities, triggers, etc. here
#   # For example, you can add a copy activity or a data flow activity
# }


# # 11. Azure Data Factory Linked Service for ACI
# # -----------------------------------------------------------------
# # This linked service allows Azure Data Factory to trigger Azure Container Instances
# # and run big data jobs using the user-assigned identity
# # -----------------------------------------------------------------
# resource "azurerm_data_factory_linked_custom_service" "aci_linked_service" {
#   name            = "AzureContainerInstanceLS"
#   data_factory_id = azurerm_data_factory.main.id
#   type            = "AzureContainerInstance"

#   type_properties_json = jsonencode({
#     resourceId = "/subscriptions/${var.subscription_id}/resourceGroups/${azurerm_resource_group.rg.name}/providers/Microsoft.ContainerInstance/containerGroups/${var.container_group_name}"
#   })

#   authentication = "UserAssignedManagedIdentity"
#   user_assigned_identity_id = azurerm_user_assigned_identity.aci_identity.id
# }






# #-------------------------------------------------------------
# # Azure Container Apps Environment
# # 1. azurerm_log_analytics_workspace    - for logging and monitoring
# # 2. azurerm_container_app_environment  - environment for apps
# # 3. azurerm_user_assigned_identity     - identity for pulling images
# # 4. azurerm_role_assignment            - assign identity to pull images 


# # resource "azurerm_log_analytics_workspace" "law" {
# resource "azurerm_log_analytics_workspace" "log" {
#   # name                = "${var.resource_group_name}-law"
#   name                = "aca-log-workspace"
#   location            = azurerm_resource_group.rg.location
#   resource_group_name = azurerm_resource_group.rg.name
#   sku                 = "PerGB2018"
#   retention_in_days   = 30
# }

# # resource "azurerm_container_app_environment" "app_env" {
# resource "azurerm_container_app_environment" "aca_env" {
#   # name                       = "${var.resource_group_name}-env"
#   name                       = "aca-env"
#   location                   = azurerm_resource_group.rg.location
#   resource_group_name        = azurerm_resource_group.rg.name
#   log_analytics_workspace_id = azurerm_log_analytics_workspace.log.id
# }

# resource "azurerm_user_assigned_identity" "aca_identity" {
#   # name                = "${var.resource_group_name}-identity"
#   name                = "aca-pull-identity"
#   resource_group_name = azurerm_resource_group.rg.name
#   location            = azurerm_resource_group.rg.location
# }

# resource "azurerm_role_assignment" "acr_pull" {
#   scope                = azurerm_container_registry.acr.id
#   role_definition_name = "AcrPull"
#   principal_id         = azurerm_user_assigned_identity.aca_identity.principal_id
# }


