#!/bin/bash
set -e

SUB_ID="$TF_VAR_subscription_id"
RG_N="$TF_VAR_resource_group_name"
RG_ID="/subscriptions/$SUB_ID/resourceGroups/$RG_N"

SA_N="$TF_VAR_storage_account_name"
SA_ID="/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.Storage/storageAccounts/$SA_N"

CR_N="$TF_VAR_container_registry_name"
CR_ID="/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.ContainerRegistry/registries/$CR_N"

KV_N="${RG_N}-kv"
KV_ID="/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.KeyVault/vaults/$KV_N"

declare -a RESOURCES=(
  "azurerm_resource_group.rg|az group show \
    --name \"$RG_N\"|\"$RG_ID\""
  "azurerm_storage_account.storage|az storage account show \
    --name \"$SA_N\" \
    --resource-group \"$RG_N\"|\"$SA_ID\""
  "azurerm_container_registry.acr|az acr show \
    --name \"$CR_N\" \
    --resource-group \"$RG_N\"|\"$CR_ID\""
  "azurerm_key_vault.kv|az keyvault show \
    --name \"$KV_N\" \
    --resource-group \"$RG_N\"|\"$KV_ID\""
)

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


# RESOURCE_GROUP_NAME="$TF_VAR_resource_group_name"
# SUBSCRIPTION_ID="$TF_VAR_subscription_id"
# RG_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"

# # Import Resource Group
# if ! terraform state show azurerm_resource_group.rg &>/dev/null; then
#   terraform import azurerm_resource_group.rg "$RG_ID"
# else
#   echo "Resource Group already managed by Terraform. Skipping import."
# fi

# # Import Storage Account
# STORAGE_ACCOUNT_NAME="$TF_VAR_storage_account_name"
# STORAGE_ACCOUNT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"
# if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
#   if ! terraform state show azurerm_storage_account.storage &>/dev/null; then
#     echo "Importing existing storage account..."
#     terraform import azurerm_storage_account.storage "$STORAGE_ACCOUNT_ID"
#   else
#     echo "Storage account already managed by Terraform. Skipping import."
#   fi
# else
#   echo "Storage account does not exist. Skipping import."
# fi

# # Import Container Registry
# CONTAINER_REGISTRY_NAME="$TF_VAR_container_registry_name"
# CONTAINER_REGISTRY_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.ContainerRegistry/registries/$CONTAINER_REGISTRY_NAME"
# if az acr show --name "$CONTAINER_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
#   if ! terraform state show azurerm_container_registry.acr &>/dev/null; then
#     echo "Importing existing container registry..."
#     terraform import azurerm_container_registry.acr "$CONTAINER_REGISTRY_ID"
#   else
#     echo "Container registry already managed by Terraform. Skipping import."
#   fi
# else
#   echo "Container registry does not exist. Skipping import."
# fi

# # Import Key Vault
# KEY_VAULT_NAME="${RESOURCE_GROUP_NAME}-kv"
# KEY_VAULT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"
# if az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
#   if ! terraform state show azurerm_key_vault.kv &>/dev/null; then
#     echo "Importing existing key vault..."
#     terraform import azurerm_key_vault.kv "$KEY_VAULT_ID"
#   else
#     echo "Key vault already managed by Terraform. Skipping import."
#   fi
# else
#   echo "Key vault does not exist. Skipping import."
# fi

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
    echo "❌ Secret '$secret_name' does not exist. Skipping."
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

