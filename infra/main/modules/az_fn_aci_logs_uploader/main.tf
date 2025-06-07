###  Azure Funtion App for ACI Logs Uploader Resources

data "azurerm_client_config" "current" {}

# Null resource to ensure dependencies are created before the function app
# This is a workaround to ensure the Key Vault is created before the Function App
resource "null_resource" "dependency_guard" {
  depends_on = [var.dependency_resources]
}


# Service Plan for Azure Function App
resource "azurerm_service_plan" "function_plan" {
  name                = var.service_plan_name
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = "Y1"    # Consumption plan for serverless functions
}

# Azure Linux Function App for ACI Logs Uploader
resource "azurerm_linux_function_app" "aci_logs_uploader" {
    name                       = var.function_app_name
    location                   = var.location
    resource_group_name        = var.resource_group_name
    service_plan_id            = azurerm_service_plan.function_plan.id
    storage_account_name       = var.storage_account_name
    # storage_account_access_key = azurerm_storage_account.storage.primary_access_key     # Uncomment if string authorization is needed

    identity {
        type = "SystemAssigned"
    }

    site_config {
        application_stack {
            python_version = "3.11"
        }
    }

    app_settings = {
        "FUNCTIONS_WORKER_RUNTIME"        = "python"
        "FUNCTION_KEY"                    = var.function_key                              # Key for the function app - create one!
        "AZURE_STORAGE_ACCOUNT"           = var.storage_account_name
        "AZURE_KEY_VAULT_URL"             = var.key_vault_uri
        "AZURE_KEY_VAULT_SECRET_NAME"     = var.blob_connection_string_name
        "BLOB_CONTAINER_NAME"             = var.blob_container_name_aci_logs
    }

    depends_on = [
        azurerm_service_plan.function_plan,
        # azurerm_key_vault.kv
        null_resource.dependency_guard
    ]
}


# Access Policy for Function App to Key Vault
resource "azurerm_key_vault_access_policy" "fn_access" {
    key_vault_id = var.key_vault_id
    tenant_id    = data.azurerm_client_config.current.tenant_id
    object_id    = azurerm_linux_function_app.aci_logs_uploader.identity[0].principal_id

    depends_on = [
        azurerm_linux_function_app.aci_logs_uploader,
        # azurerm_key_vault.kv
        null_resource.dependency_guard
    ]

    secret_permissions = ["Get"]
}


# Role Assignment for Function App to Storage Account 
# - allows reading/writing blobs without needing a connection string
resource "azurerm_role_assignment" "fn_storage_role" {
    scope                = var.storage_account_id
    role_definition_name = "Storage Blob Data Contributor"                                      # Allows read/write access to blobs
    principal_id         = azurerm_linux_function_app.aci_logs_uploader.identity[0].principal_id   # Fn App Managed Identity

    depends_on = [
        azurerm_linux_function_app.aci_logs_uploader
    ]
}


# Role Assignment for GitHub Actions to Function App
# - allows GitHub Actions to authenticate with the Function App
resource "azurerm_role_assignment" "github_deploy_rights" {
    scope                = azurerm_linux_function_app.aci_logs_uploader.id
    role_definition_name = "Contributor"           # Allows deployment rights
    principal_id         = var.github_oidc_sp_id   # GitHub OIDC Service Principal ID

    depends_on = [
        azurerm_linux_function_app.aci_logs_uploader
    ]
}
