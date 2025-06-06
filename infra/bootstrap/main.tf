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

  depends_on = [
    azurerm_resource_group.rg
  ]
}

# 3.A. STORAGE CONTAINER FOR TERRAFORM STATE
# This container will store the Terraform state files
resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"

  depends_on = [
    azurerm_storage_account.storage
  ]
}

# 3.B. Create a storage container for Whisperer files
# This serves as a sink for the project's results and outputs
resource "azurerm_storage_container" "whisperer" {
  name                  = "whisperer"
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"

  depends_on = [
    azurerm_storage_account.storage
  ]
}

# 3.C. Create a storage container for ACI logs
# This container will store logs from ephemeral Azure Container Instances (ACI)
resource "azurerm_storage_container" "aci_logs" {
  name                  = "aci-logs"
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"

  depends_on = [
    azurerm_storage_account.storage
  ]
}

# 4. Automatically set GitHub secrets
resource "github_actions_secret" "resource_group_name" {
  repository      = var.github_repository
  secret_name     = "AZURE_RESOURCE_GROUP"
  plaintext_value = azurerm_resource_group.rg.name

  depends_on = [
    azurerm_resource_group.rg
  ]
}

resource "github_actions_secret" "storage_account_name" {
  repository      = var.github_repository
  secret_name     = "STORAGE_ACCOUNT_NAME"
  plaintext_value = azurerm_storage_account.storage.name

  depends_on = [
    azurerm_storage_account.storage
  ]
}


data "azurerm_subscription" "current" {}

# Add this instead
resource "azuread_application" "github_actions" {
  display_name = "github-actions-app"
}

resource "azuread_service_principal" "github_actions" {
  client_id = azuread_application.github_actions.client_id
}

resource "azuread_application_federated_identity_credential" "github_actions" {
  application_id = azuread_application.github_actions.id
  display_name   = "github-actions-federated-credential"
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_owner}/${var.github_repository}:ref:refs/heads/main" # adjust branch if needed
  audiences      = ["api://AzureADTokenExchange"]
}


resource "azurerm_role_assignment" "github_actions_user_access_administrator" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "User Access Administrator"
  principal_id         = azuread_service_principal.github_actions.object_id
}

resource "azurerm_role_assignment" "github_actions_role_assignment_admin" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Role Based Access Control Administrator"
  principal_id         = azuread_service_principal.github_actions.object_id
}

resource "azurerm_role_assignment" "github_actions_subscription_contributor" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}

# FIX: Use service principal, not managed identity
resource "azurerm_role_assignment" "github_actions_rg_contributor" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id  # CHANGED
}

# For deploying Azure Function Apps, we need the "Contributor" in the storage account
resource "azurerm_role_assignment" "github_actions_storage_blob_data_contributor" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}


# Output both client_id and object_id for the second flow
output "client_id" {
  value = azuread_application.github_actions.client_id
}

output "service_principal_object_id" {
  value = azuread_service_principal.github_actions.object_id
}

# FIX: Use app registration client ID
resource "github_actions_secret" "github_actions_client_id" {
  repository      = var.github_repository
  secret_name     = "AZURE_CLIENT_ID"
  plaintext_value = azuread_application.github_actions.client_id  # CHANGED
}

# Add the object_id as a secret too for the second flow
resource "github_actions_secret" "github_actions_object_id" {
  repository      = var.github_repository
  secret_name     = "AZURE_OBJECT_ID"
  plaintext_value = azuread_service_principal.github_actions.object_id
}


# 8. Register the Microsoft.App provider for Container Apps
# This is necessary for using Azure Container Apps, which is a newer service.
resource "null_resource" "register_containerapps" {
  provisioner "local-exec" {
    command = "az provider register -n Microsoft.App --wait"
  }

  triggers = {
    # always_run = timestamp()  # Ensures this runs every time you apply
    rg_name = azurerm_resource_group.rg.name # This ensures it runs after the resource group is created
  }

  depends_on = [
    azurerm_resource_group.rg
  ]
}

data "azurerm_client_config" "current" {}

