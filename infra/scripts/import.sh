#!/bin/bash

set -e

# ---------------------------------------------------------
# Get the absolute path of the directory containing this script
# and set the path to the utils directory
# ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS_DIR="$SCRIPT_DIR/utils"
# ---------------------------------------------------------


# ---------------------------------------------------------
# Script to import existing Azure resources into Terraform state
# ----------------------------------------------------------

SUB_ID="$TF_VAR_subscription_id"
RG_N="$TF_VAR_resource_group_name"
RG_ID="/subscriptions/$SUB_ID/resourceGroups/$RG_N"

SA_N="$TF_VAR_storage_account_name"
SA_ID="$RG_ID/providers/Microsoft.Storage/storageAccounts/$SA_N"

CR_N="$TF_VAR_container_registry_name"
CR_ID="$RG_ID/providers/Microsoft.ContainerRegistry/registries/$CR_N"

KV_N="${RG_N}-kv"
KV_ID="$RG_ID/providers/Microsoft.KeyVault/vaults/$KV_N"


declare -a RESOURCES=(
  "azurerm_resource_group.rg|az group show --name \"$RG_N\"|\"$RG_ID\""
  "azurerm_storage_account.storage|az storage account show --name \"$SA_N\" --resource-group \"$RG_N\"|\"$SA_ID\""
  "azurerm_container_registry.acr|az acr show --name \"$CR_N\" --resource-group \"$RG_N\"|\"$CR_ID\""
  "azurerm_key_vault.kv|az keyvault show --name \"$KV_N\" --resource-group \"$RG_N\"|\"$KV_ID\""
)

# ---------------------------------------------------------
# Import Azure Data Factory and Managed Identities
# ----------------------------------------------------------

ADF_N="${RG_N}-adf"
ADF_ID="$RG_ID/providers/Microsoft.DataFactory/factories/$ADF_N"

ACI_IDENTITY_N="${RG_N}-aci-identity"
ACI_IDENTITY_ID="$RG_ID/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$ACI_IDENTITY_N"

KV_IDENTITY_N="${RG_N}-key-vault-identity"
KV_IDENTITY_ID="$RG_ID/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$KV_IDENTITY_N"

STORAGE_IDENTITY_N="${RG_N}-storage-identity"
STORAGE_IDENTITY_ID="$RG_ID/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$STORAGE_IDENTITY_N"

RESOURCES+=(
  "azurerm_data_factory.adf|az datafactory factory show --name \"$ADF_N\" --resource-group \"$RG_N\"|\"$ADF_ID\""
  "azurerm_user_assigned_identity.aci_identity|az identity show --name \"$ACI_IDENTITY_N\" --resource-group \"$RG_N\"|\"$ACI_IDENTITY_ID\""
  "azurerm_user_assigned_identity.key_vault_identity|az identity show --name \"$KV_IDENTITY_N\" --resource-group \"$RG_N\"|\"$KV_IDENTITY_ID\""
  "azurerm_user_assigned_identity.storage_identity|az identity show --name \"$STORAGE_IDENTITY_N\" --resource-group \"$RG_N\"|\"$STORAGE_IDENTITY_ID\""
)







# ---------------------------------------------------------
# Import Azure Function App and related resources
# ----------------------------------------------------------

# Service Plan for Azure Function App
SP_N="aci-fn-plan"
SP_ID="$RG_ID/providers/Microsoft.Web/serverfarms/$SP_N"
MODULE="module.aci_logs_uploader"
RESOURCES+=(
  "$MODULE.azurerm_service_plan.function_plan|az appservice plan show --name \"$SP_N\" --resource-group \"$RG_N\"|\"$SP_ID\""
)

# Azure Function App
AF_N="aci-logs-uploader"
AF_ID="$RG_ID/providers/Microsoft.Web/sites/$AF_N"
RESOURCES+=(
  "$MODULE.azurerm_linux_function_app.aci_logs_uploader|az functionapp show --name \"$AF_N\" --resource-group \"$RG_N\"|\"$AF_ID\""
)





# # Access Policy for Function App to Key Vault
# resource "azurerm_key_vault_access_policy" "fn_access" {
#     key_vault_id = var.key_vault_id
#     tenant_id    = data.azurerm_client_config.current.tenant_id
#     object_id    = azurerm_linux_function_app.aci_logs_uploader.identity[0].principal_id

#     depends_on = [
#         azurerm_linux_function_app.aci_logs_uploader,
#         # azurerm_key_vault.kv
#         null_resource.dependency_guard
#     ]

#     secret_permissions = ["Get"]
# }

# Import Access Policy for Data Factory to Key Vault
APDFKV_N="${RG_N}-adf-kv-access-policy"
APDFKV_ID="$RG_ID/providers/Microsoft.KeyVault/vaults/$KV_N/accessPolicies/$APDFKV_N"
RESOURCES+=(
  "$MODULE.azurerm_key_vault_access_policy.adf_kv_access_policy|az keyvault access-policy show --name \"$APDFKV_N\" --vault-name \"$KV_N\" --resource-group \"$RG_N\"|\"$APDFKV_ID\""
)


# # Role Assignment for GitHub Actions to Function App
# # - allows GitHub Actions to authenticate with the Function App
# resource "azurerm_role_assignment" "github_deploy_rights" {
#     scope                = azurerm_linux_function_app.aci_logs_uploader.id
#     role_definition_name = "Contributor"           # Allows deployment rights
#     principal_id         = var.github_oidc_sp_id   # GitHub OIDC Service Principal ID

#     depends_on = [
#         azurerm_linux_function_app.aci_logs_uploader
#     ]
# }

# Import GitHub Actions role assignment for Function App
GH_AF_ROLE_N="${RG_N}-gh-actions-fn-role"
GH_AF_ROLE_ID="$RG_ID/providers/Microsoft.Web/sites/$AF_N/providers/Microsoft.Authorization/roleAssignments/$GH_AF_ROLE_N"
RESOURCES+=(
  "$MODULE.azurerm_role_assignment.github_actions_function_app|az role assignment show --name \"$GH_AF_ROLE_N\" --scope \"/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.Web/sites/$AF_N\"|\"$GH_AF_ROLE_ID\""
)



# # Linked Service to Azure Data Factory for the Function App
# resource "azurerm_data_factory_linked_service_azure_function" "aci_logs_fn" {
#   name                = "AzureFunctionAciLogsLinkedService"
#   data_factory_id     = azurerm_data_factory.adf.id
#   url                 = "https://${azurerm_function_app.aci_logs_uploader.default_hostname}"

#   # Option 1: Use direct function key
#   key             = var.function_key

#   # Option 2 (recommended): Use Key Vault
#   # key_vault_key {
#   #   linked_service_name = azurerm_data_factory_linked_service_azure_key_vault.example.name
#   #   secret_name         = azurerm_key_vault_secret.function_key.name
#   # }

#   depends_on = [module.aci_logs_uploader]
# }
# Import Linked Service for Data Factory to Function App

AF_LS_N="${RG_N}-adf-fn-linked-service"
AF_LS_ID="$RG_ID/providers/Microsoft.DataFactory/factories/$ADF_N/linkedservices/$AF_LS_N"
RESOURCES+=(
  "azurerm_data_factory_linked_service_azure_function.adf_fn_linked_service|az datafactory linked-service show --name \"$AF_LS_N\" --factory-name \"$ADF_N\" --resource-group \"$RG_N\"|\"$AF_LS_ID\""
)

#----------------------------------------------------------
# > Execute the import commands for each resource
#----------------------------------------------------------
for entry in "${RESOURCES[@]}"; do
  IFS="|" read -r tf_name check_cmd res_id <<< "$entry"

  echo "Checking $tf_name..."
  if eval "$check_cmd --subscription $TF_VAR_subscription_id" &>/dev/null; then
    if terraform state show "$tf_name" &>/dev/null; then
      echo "$tf_name already managed. Skipping."
    else
      terraform import "$tf_name" "$res_id"
    fi
  else
    echo "$tf_name does not exist. Skipping."
  fi
done


# ----------------------------------------------------------
# Role Assignments for Azure Function App
# ----------------------------------------------------------

SP_OBJECT_ID=$(az functionapp identity show --name "$AF_N" --resource-group "$RG_N" --query principalId -o tsv)

# - Storage Data Owner Role Assignment
# Allows file share creation
source "$UTILS_DIR/import-role-asgn.sh" "$SP_OBJECT_ID" \
  "fn_storage_data_owner" \
  "/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.Storage/storageAccounts/$SA_N" \
  "Storage Account Contributor" \
  "aci_logs_uploader"

# - Storage Blob Data Contributor Role Assignment
# Allows read/write access to blobs
source "$UTILS_DIR/import-role-asgn.sh" "$SP_OBJECT_ID" \
  "fn_storage_role" \
  "/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.Storage/storageAccounts/$SA_N" \
  "Storage Blob Data Contributor" \
  "aci_logs_uploader"




# ------------------------------------------------
# Function to import Key Vault secrets into Terraform state
# ------------------------------------------------

import_kv_secret() {
  local tf_name="$1"        # Terraform resource name (e.g. acr_username)
  local secret_name="$2"    # Azure secret name (e.g. acr-admin-username)

  echo "Checking secret '$secret_name'..."

  local secret_id
  secret_id=$(az keyvault secret show \
    --name "$secret_name" \
    --vault-name "$KEY_VAULT_NAME" \
    --subscription "$SUBSCRIPTION_ID" \
    --query "id" -o tsv 2>/dev/null || echo "")

  if [[ -z "$secret_id" ]]; then
    echo "❌ Secret '$secret_name' does not exist. Skipping." # RUNS FOR EVERY SECRET - DEBUG THIS
    return
  fi

  echo "✅ Secret '$secret_name' exists in Azure."

  if terraform state show "azurerm_key_vault_secret.$tf_name" &>/dev/null; then
    echo "🔁 Secret '$tf_name' already managed by Terraform. Skipping import."
  else
    echo "📥 Importing secret '$secret_name' as '$tf_name'..."
    terraform import "azurerm_key_vault_secret.$tf_name" "$secret_id"
  fi
}



# Import ACR username secret
ACR_USERNAME_SECRET_NAME="acr-admin-username"
import_kv_secret "acr_username" "$ACR_USERNAME_SECRET_NAME"

ACR_PASSWORD_SECRET_NAME="acr-admin-password"
import_kv_secret "acr_password" "$ACR_PASSWORD_SECRET_NAME"

BLOB_CONNECTION_STRING_SECRET_NAME="blob-storage-connection-string"
import_kv_secret "blob_connection_string" "$BLOB_CONNECTION_STRING_SECRET_NAME"

# Podcast API secrets
import_kv_secret "podcast_api_key" "PodcastingIndexApiKey"
import_kv_secret "podcast_api_secret" "PodcastingIndexApiSecret"

