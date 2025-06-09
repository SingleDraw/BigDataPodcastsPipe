
# THESE WER USER ASSIGNED IDENTITIES
# # Loop through user-assigned identities and assign roles
# # This allows the Data Factory to access the resource group and other resources
# locals {
#   user_assigned_identities = {
#     storage   = azurerm_user_assigned_identity.storage_identity.principal_id
#     keyvault  = azurerm_user_assigned_identity.key_vault_identity.principal_id
#   }
# }
# resource "azurerm_role_assignment" "adf_contributors" {
#   for_each             = local.user_assigned_identities
#   scope                = azurerm_resource_group.rg.id
#   role_definition_name = "Contributor"
#   principal_id         = each.value
# }

# # Role assignment for Data Factory to access the resource group
# resource "azurerm_role_assignment" "adf_contributor" {
#   scope                = azurerm_resource_group.rg.id
#   role_definition_name = "Contributor"
#   # Reference to the User Assigned Identity defined inside the Data Factory resource
#   # System assigned identity is not used here
#   # principal_id         = azurerm_data_factory.adf.identity[0].principal_id 
#   # So we use the user-assigned identity
#   principal_id         = azurerm_user_assigned_identity.storage_identity.principal_id
# }

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


