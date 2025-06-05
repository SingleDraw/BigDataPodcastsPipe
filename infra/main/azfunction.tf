# # Azure Funtion App for ACI Logs Uploader Resources

# # Service Plan for Azure Function App
# resource "azurerm_app_service_plan" "function_plan" {
#   name                = "aci-fn-plan"
#   location            = azurerm_resource_group.rg.location
#   resource_group_name = azurerm_resource_group.rg.name
#   kind                = "FunctionApp"
#   reserved            = true  # Required for Linux

#   sku {
#     tier = "Dynamic"  # Consumption plan for serverless functions
#     size = "Y1"       # Consumption plan size
#   }
# }



# # Azure Linux Function App for ACI Logs Uploader
# resource "azurerm_linux_function_app" "aci_logs_uploader" {
#     name                       = "aci-logs-uploader"
#     location                   = azurerm_resource_group.rg.location
#     resource_group_name        = azurerm_resource_group.rg.name
#     service_plan_id            = azurerm_app_service_plan.function_plan.id
#     storage_account_name       = var.storage_account_name
#     # storage_account_access_key = azurerm_storage_account.storage.primary_access_key     # Uncomment if string authorization is needed

#     identity {
#         type = "SystemAssigned"
#     }

#     site_config {
#         application_stack {
#         python_version = "3.11"
#         }
#     }

#     app_settings = {
#         "FUNCTIONS_WORKER_RUNTIME"        = "python"
#         "FUNCTION_KEY"                    = var.function_key                                # Key for the function app - create one!
#         "AZURE_STORAGE_ACCOUNT"           = var.storage_account_name
#         "AZURE_KEY_VAULT_URL"             = azurerm_key_vault.kv.vault_uri
#         "AZURE_KEY_VAULT_SECRET_NAME"     = var.blob_connection_string_name
#         "BLOB_CONTAINER_NAME"             = var.blob_container_name_aci_logs
#     }

#     depends_on = [
#         azurerm_app_service_plan.function_plan,
#         azurerm_key_vault.kv
#     ]
# }

# # Access Policy for Function App to Key Vault
# resource "azurerm_key_vault_access_policy" "fn_access" {
#     key_vault_id = azurerm_key_vault.kv.id
#     tenant_id    = data.azurerm_client_config.current.tenant_id
#     object_id    = azurerm_linux_function_app.aci_logs_uploader.identity.principal_id

#     depends_on = [
#         azurerm_linux_function_app.aci_logs_uploader,
#         azurerm_key_vault.kv
#     ]

#     secret_permissions = ["get"]
# }

# # Role Assignment for Function App to Storage Account 
# # - allows reading/writing blobs without needing a connection string
# resource "azurerm_role_assignment" "fn_storage_role" {
#     scope                = azurerm_storage_account.storage.id
#     role_definition_name = "Storage Blob Data Contributor"  # Allows read/write access to blobs
#     principal_id         = azurerm_linux_function_app.aci_logs_uploader.identity.principal_id

#     depends_on = [
#         azurerm_linux_function_app.aci_logs_uploader
#     ]
# }




# # Role Assignment for GitHub Actions to Function App
# # - allows GitHub Actions to authenticate with the Function App
# resource "azurerm_role_assignment" "github_deploy_rights" {
#     scope                = azurerm_linux_function_app.aci_logs_uploader.id
#     role_definition_name = "Contributor"
#     principal_id         = azurerm_user_assigned_identity.github_actions.principal_id

#     depends_on = [
#         azurerm_federated_identity_credential.github_oidc,
#         azurerm_linux_function_app.aci_logs_uploader
#     ]
# }
