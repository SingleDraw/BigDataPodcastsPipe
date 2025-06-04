Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create
Terraform will perform the following actions:
  # azurerm_data_factory.adf will be created
  + resource "azurerm_data_factory" "adf" ***
      + id                     = (known after apply)
      + location               = "***"
      + name                   = "***-adf"
      + public_network_enabled = true
      + resource_group_name    = "***"
      + identity ***
          + identity_ids = (known after apply)
          + principal_id = (known after apply)
          + tenant_id    = (known after apply)
          + type         = "UserAssigned"
        ***
    ***
  # azurerm_key_vault_secret.podcast_api_key will be created
  + resource "azurerm_key_vault_secret" "podcast_api_key" ***
      + id                      = (known after apply)
      + key_vault_id            = "/subscriptions/***/resourceGroups/***/providers/Microsoft.KeyVault/vaults/***-kv"
      + name                    = "PodcastingIndexApiKey"
      + resource_id             = (known after apply)
      + resource_versionless_id = (known after apply)
      + value                   = (sensitive value)
      + value_wo                = (write-only attribute)
      + version                 = (known after apply)
      + versionless_id          = (known after apply)
    ***
  # azurerm_key_vault_secret.podcast_api_secret will be created
  + resource "azurerm_key_vault_secret" "podcast_api_secret" ***
      + id                      = (known after apply)
      + key_vault_id            = "/subscriptions/***/resourceGroups/***/providers/Microsoft.KeyVault/vaults/***-kv"
      + name                    = "PodcastingIndexApiSecret"
      + resource_id             = (known after apply)
      + resource_versionless_id = (known after apply)
      + value                   = (sensitive value)
      + value_wo                = (write-only attribute)
      + version                 = (known after apply)
      + versionless_id          = (known after apply)
    ***
  # azurerm_role_assignment.aci_identity_role will be created
  + resource "azurerm_role_assignment" "aci_identity_role" ***
      + condition_version                = (known after apply)
      + id                               = (known after apply)
      + name                             = (known after apply)
      + principal_id                     = (known after apply)
      + principal_type                   = (known after apply)
      + role_definition_id               = (known after apply)
      + role_definition_name             = "AcrPull"
      + scope                            = "/subscriptions/***/resourceGroups/***/providers/Microsoft.ContainerRegistry/registries/***"
      + skip_service_principal_aad_check = (known after apply)
    ***
  # azurerm_role_assignment.aci_storage_role will be created
  + resource "azurerm_role_assignment" "aci_storage_role" ***
      + condition_version                = (known after apply)
      + id                               = (known after apply)
      + name                             = (known after apply)
      + principal_id                     = (known after apply)
      + principal_type                   = (known after apply)
      + role_definition_id               = (known after apply)
      + role_definition_name             = "Storage Blob Data Contributor"
      + scope                            = "/subscriptions/***/resourceGroups/***/providers/Microsoft.Storage/storageAccounts/***"
      + skip_service_principal_aad_check = (known after apply)
    ***
  # azurerm_role_assignment.adf_contributor will be created
  + resource "azurerm_role_assignment" "adf_contributor" ***
      + condition_version                = (known after apply)
      + id                               = (known after apply)
      + name                             = (known after apply)
      + principal_id                     = (known after apply)
      + principal_type                   = (known after apply)
      + role_definition_id               = (known after apply)
      + role_definition_name             = "Contributor"
      + scope                            = "/subscriptions/***/resourceGroups/***"
      + skip_service_principal_aad_check = (known after apply)
    ***
2025-06-04T07:51:48.579Z [DEBUG] HEAD https://***.blob.core.windows.net/tfstate/terraform.tfstate
  # azurerm_role_assignment.key_vault_identity_role will be created
  + resource "azurerm_role_assignment" "key_vault_identity_role" ***
      + condition_version                = (known after apply)
      + id                               = (known after apply)
      + name                             = (known after apply)
      + principal_id                     = (known after apply)
      + principal_type                   = (known after apply)
      + role_definition_id               = (known after apply)
      + role_definition_name             = "Key Vault Secrets User"
      + scope                            = "/subscriptions/***/resourceGroups/***/providers/Microsoft.KeyVault/vaults/***-kv"
      + skip_service_principal_aad_check = (known after apply)
    ***
  # azurerm_role_assignment.storage_identity_role will be created
  + resource "azurerm_role_assignment" "storage_identity_role" ***
      + condition_version                = (known after apply)
      + id                               = (known after apply)
      + name                             = (known after apply)
      + principal_id                     = (known after apply)
      + principal_type                   = (known after apply)
      + role_definition_id               = (known after apply)
      + role_definition_name             = "Storage Blob Data Contributor"
      + scope                            = "/subscriptions/***/resourceGroups/***/providers/Microsoft.Storage/storageAccounts/***"
      + skip_service_principal_aad_check = (known after apply)
    ***
  # azurerm_user_assigned_identity.aci_identity will be created
  + resource "azurerm_user_assigned_identity" "aci_identity" ***
      + client_id           = (known after apply)
      + id                  = (known after apply)
      + location            = "***"
      + name                = "***-aci-identity"
      + principal_id        = (known after apply)
      + resource_group_name = "***"
      + tenant_id           = (known after apply)
    ***
  # azurerm_user_assigned_identity.key_vault_identity will be created
  + resource "azurerm_user_assigned_identity" "key_vault_identity" ***
      + client_id           = (known after apply)
      + id                  = (known after apply)
      + location            = "***"
      + name                = "***-key-vault-identity"
      + principal_id        = (known after apply)
      + resource_group_name = "***"
      + tenant_id           = (known after apply)
    ***
  # azurerm_user_assigned_identity.storage_identity will be created
  + resource "azurerm_user_assigned_identity" "storage_identity" ***
      + client_id           = (known after apply)
      + id                  = (known after apply)
      + location            = "***"
      + name                = "***-storage-identity"
      + principal_id        = (known after apply)
      + resource_group_name = "***"
      + tenant_id           = (known after apply)
    ***
  # github_actions_secret.aci_identity_id will be created
  + resource "github_actions_secret" "aci_identity_id" ***
      + created_at      = (known after apply)
      + id              = (known after apply)
      + plaintext_value = (sensitive value)
      + repository      = "BigDataPodcastsPipe"
      + secret_name     = "IDENTITY_RESOURCE_ID"
      + updated_at      = (known after apply)
    ***
  # github_actions_secret.adf_name will be created
  + resource "github_actions_secret" "adf_name" ***
      + created_at      = (known after apply)
      + id              = (known after apply)
      + plaintext_value = (sensitive value)
      + repository      = "BigDataPodcastsPipe"
      + secret_name     = "ADF_NAME"
      + updated_at      = (known after apply)
    ***
Plan: 13 to add, 0 to change, 0 to destroy.