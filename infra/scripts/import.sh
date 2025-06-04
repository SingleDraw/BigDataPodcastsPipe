#!/bin/bash
set -e

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
ACR_USERNAME_SECRET_NAME="acr-username"
import_kv_secret "acr_username" "$ACR_USERNAME_SECRET_NAME"

ACR_PASSWORD_SECRET_NAME="acr-password"
import_kv_secret "acr_password" "$ACR_PASSWORD_SECRET_NAME"

BLOB_CONNECTION_STRING_SECRET_NAME="blob-storage-connection-string"
import_kv_secret "blob_connection_string" "$BLOB_CONNECTION_STRING_SECRET_NAME"

