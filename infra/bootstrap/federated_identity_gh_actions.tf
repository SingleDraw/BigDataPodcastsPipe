# Federated Identity for GitHub Actions
# In GitHub → Settings → Secrets and variables → Actions → Create repository secrets:
# Name	Value
# AZURE_CLIENT_ID	azurerm_user_assigned_identity.github_actions.client_id
# AZURE_SUBSCRIPTION_ID	Your Azure subscription ID
# AZURE_TENANT_ID	Your Azure tenant ID
# FUNCTION_APP_NAME	aci-logs-uploader
# RESOURCE_GROUP	your RG name

# Then in workflow file:
    # - name: Log in to Azure
    #   uses: azure/login@v1
    #   with:
    #     client-id: ${{ secrets.AZURE_CLIENT_ID }}
    #     tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    #     subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

# resource "azurerm_user_assigned_identity" "github_actions" {
#     name                = "github-actions-identity"
#     resource_group_name = azurerm_resource_group.rg.name
#     location            = azurerm_resource_group.rg.location

#     tags = {
#         environment = "GitHub Actions"
#     }

#     depends_on = [
#         azurerm_resource_group.rg
#     ]
# }

# resource "azurerm_federated_identity_credential" "github_oidc" {
#     name                = "github-actions-oidc"
#     resource_group_name = azurerm_resource_group.rg.name
#     parent_id           = azurerm_user_assigned_identity.github_actions.id
#     audience            = ["api://AzureADTokenExchange"]
#     issuer              = "https://token.actions.githubusercontent.com"
#     subject             = "repo:${var.github_owner}/${var.github_repository}:ref:refs/heads/main" # adjust branch if needed

#     depends_on = [
#         azurerm_user_assigned_identity.github_actions
#     ]
# }

# # # in function app resource definition, add identity block:
# # resource "azurerm_role_assignment" "github_deploy_rights" {
# #     scope                = azurerm_linux_function_app.aci_logs_uploader.id
# #     role_definition_name = "Contributor"
# #     principal_id         = azurerm_user_assigned_identity.github_actions.principal_id

# #     depends_on = [
# #         azurerm_federated_identity_credential.github_oidc,
# #         azurerm_linux_function_app.aci_logs_uploader
# #     ]
# # }
