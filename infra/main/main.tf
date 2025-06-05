
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


# Get the current client configuration (OIDC identity)
# This ensures we can set access policies for the Key Vault for the current user
# If previously KV was created with service principal, 
# this will overwrite it with the current user's identity
data "azurerm_client_config" "current" {}

# 4. KV - Azure Key Vault
# -----------------------------------------------------------------
resource "azurerm_key_vault" "kv" {
  name                = "${var.resource_group_name}-kv"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  enable_rbac_authorization = true  # Enable RBAC instead of access policies

  depends_on = [
    azurerm_resource_group.rg,
    azurerm_client_config.current
  ]

  # Admin access policy for the current user
  # access_policy {
  #   tenant_id = data.azurerm_client_config.current.tenant_id
  #   object_id = data.azurerm_client_config.current.object_id
  #   secret_permissions = [
  #     "Get", "List", "Set", "Delete"
  #   ]
  # }
}

# Assign Key Vault Secrets Officer role to the current identity
resource "azurerm_role_assignment" "kv_secrets_officer" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Podcasting Index Api Secrets
resource "azurerm_key_vault_secret" "podcast_api_key" {
  name         = "PodcastingIndexApiKey"
  value        = var.podcasting_index_api_key
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_key_vault.kv]
}

resource "azurerm_key_vault_secret" "podcast_api_secret" {
  name         = "PodcastingIndexApiSecret"
  value        = var.podcasting_index_api_secret
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_key_vault.kv]
}

# Store ACR credentials in Key Vault
resource "azurerm_key_vault_secret" "acr_username" {
  name         = "acr-admin-username"
  value        = azurerm_container_registry.acr.admin_username
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_key_vault.kv]
}

resource "azurerm_key_vault_secret" "acr_password" {
  name         = "acr-admin-password"
  value        = azurerm_container_registry.acr.admin_password
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_key_vault.kv]
}

# Store storage connection string
resource "azurerm_key_vault_secret" "blob_connection_string" {
  name         = var.blob_connection_string_name
  value        = azurerm_storage_account.storage.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_key_vault.kv]
}



#-------------------------------------------------------------
# 7. UIAMs === User-Assigned Managed Identity - Storage Account
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

#  ACI identity → Container Instance Contributor on the resource group
# data "azurerm_role_definition" "aci_contributor" {
#   name = "f1a07417-d97a-45cb-824c-7a7467783830"
# }

resource "azurerm_user_assigned_identity" "aci_identity" {                      # <---------- UAMI FOR ACI
  name                = "aci-uami"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
}

resource "azurerm_key_vault_access_policy" "aci_identity_policy" {              # <---------- UAMI FOR ACI
  # This policy allows the ACI identity to access Key Vault secrets
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.aci_identity.principal_id

  secret_permissions = ["Get"]
}

resource "azurerm_role_assignment" "aci_identity_role" {
  # This role assignment allows the ACI identity to pull images from ACR
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aci_identity.principal_id
}

resource "azurerm_role_assignment" "aci_storage_role" {
  # This role assignment allows the ACI identity to read/write to the storage account
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.aci_identity.principal_id
}

resource "azurerm_role_assignment" "aci_identity_contributor" {
  # This role assignment allows the ACI identity to create/manage container instances
  # Useful if want to run or delete ACI from inside the container
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.aci_identity.principal_id
}


# 6. Automatically set GitHub secrets
# This section sets GitHub secrets automatically using the GitHub Actions Secrets API
# Ensure you have the GitHub Actions provider configured in your Terraform setup
#-------------------------------------------------------------

# # # Update the GitHub secret to use client ID of the ACI identity       # <---------- UAMI FOR ACI
resource "github_actions_secret" "aci_identity_client_id" {
  repository      = var.github_repository
  secret_name     = "IDENTITY_CLIENT_ID"
  plaintext_value = azurerm_user_assigned_identity.aci_identity.client_id
}

# Aci Identity Resource ID for the container identity                     # <---------- UAMI FOR ACI
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
  plaintext_value = azurerm_container_registry.acr.admin_username
}

resource "github_actions_secret" "acr_password" {
  repository      = var.github_repository
  secret_name     = "ACR_PASSWORD"
  plaintext_value = azurerm_container_registry.acr.admin_password
}

# Resources names
resource "github_actions_secret" "key_vault_name" {
  repository      = var.github_repository
  secret_name     = "KEY_VAULT_NAME"
  plaintext_value = azurerm_key_vault.kv.name
}

# Storage Secret Key [ STORAGE_ACCOUNT_NAME is already set in GitHub secrets from initial .env file ]
resource "github_actions_secret" "stortage_account_key" {
  repository      = var.github_repository
  secret_name     = "STORAGE_ACCOUNT_KEY"
  plaintext_value = azurerm_storage_account.storage.primary_access_key
}

#-------------------------------------------------------------
# 10. Azure Data Factory - Big Data Pipeline Runner
# -----------------------------------------------------------------
# This section sets up Azure Data Factory to run big data pipelines
resource "azurerm_data_factory" "adf" {
  name                = "${var.resource_group_name}-adf"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  identity {
    type = "SystemAssigned"
  }
}

# We need to read the Data Factory identity after creation cause its identity is not available until after creation
# This data source allows us to reference the Data Factory's system-assigned identity thanks to the `depends_on` block
# This is necessary to ensure the Data Factory is created before we try to read its identity
data "azurerm_data_factory" "adf" {
  name                = azurerm_data_factory.adf.name
  resource_group_name = azurerm_resource_group.rg.name
  depends_on          = [azurerm_data_factory.adf] # ensures ADF is created before reading
}

# Allow ADF to pull from ACR
resource "azurerm_role_assignment" "adf_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = data.azurerm_data_factory.adf.identity[0].principal_id
}

# Allow ADF to create/manage ACI
resource "azurerm_role_assignment" "adf_aci_contributor" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Contributor"
  principal_id         = data.azurerm_data_factory.adf.identity[0].principal_id
}



# Store Azure Data Factory name in GitHub secrets
resource "github_actions_secret" "adf_name" {
  repository      = var.github_repository
  secret_name     = "ADF_NAME"
  plaintext_value = azurerm_data_factory.adf.name
}
