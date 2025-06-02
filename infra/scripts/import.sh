#!/bin/bash
set -e

RESOURCE_GROUP_NAME="$TF_VAR_resource_group_name"
SUBSCRIPTION_ID="$TF_VAR_subscription_id"
RG_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"

# Import Resource Group
if ! terraform state show azurerm_resource_group.rg &>/dev/null; then
  terraform import azurerm_resource_group.rg "$RG_ID"
else
  echo "Resource Group already managed by Terraform. Skipping import."
fi

# Import Storage Account
STORAGE_ACCOUNT_NAME="$TF_VAR_storage_account_name"
STORAGE_ACCOUNT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"
if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  if ! terraform state show azurerm_storage_account.storage &>/dev/null; then
    echo "Importing existing storage account..."
    terraform import azurerm_storage_account.storage "$STORAGE_ACCOUNT_ID"
  else
    echo "Storage account already managed by Terraform. Skipping import."
  fi
else
  echo "Storage account does not exist. Skipping import."
fi

# Import Container Registry
CONTAINER_REGISTRY_NAME="$TF_VAR_container_registry_name"
CONTAINER_REGISTRY_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.ContainerRegistry/registries/$CONTAINER_REGISTRY_NAME"
if az acr show --name "$CONTAINER_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  if ! terraform state show azurerm_container_registry.acr &>/dev/null; then
    echo "Importing existing container registry..."
    terraform import azurerm_container_registry.acr "$CONTAINER_REGISTRY_ID"
  else
    echo "Container registry already managed by Terraform. Skipping import."
  fi
else
  echo "Container registry does not exist. Skipping import."
fi

# Import Key Vault
KEY_VAULT_NAME="${RESOURCE_GROUP_NAME}-kv"
KEY_VAULT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"
if az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  if ! terraform state show azurerm_key_vault.kv &>/dev/null; then
    echo "Importing existing key vault..."
    terraform import azurerm_key_vault.kv "$KEY_VAULT_ID"
  else
    echo "Key vault already managed by Terraform. Skipping import."
  fi
else
  echo "Key vault does not exist. Skipping import."
fi

# Import ACR username secret
ACR_USERNAME_SECRET_NAME="acr-admin-username"

# Check if secret exists in Azure
ACR_USERNAME_SECRET_ID=$(az keyvault secret show \
  --name "$ACR_USERNAME_SECRET_NAME" \
  --vault-name "$KEY_VAULT_NAME" \
  --subscription "$SUBSCRIPTION_ID" \
  --query "id" -o tsv 2>/dev/null || echo "")

# Proceed if secret exists
if [[ -n "$ACR_USERNAME_SECRET_ID" ]]; then
  echo "ACR username secret exists in Azure."

  # Check if already managed by Terraform
  if terraform state show azurerm_key_vault_secret.acr_username &>/dev/null; then
    echo "Secret already managed by Terraform. Skipping import."
  else
    echo "Importing existing ACR username secret..."
    terraform import azurerm_key_vault_secret.acr_username "$ACR_USERNAME_SECRET_ID"
  fi
else
  echo "ACR username secret does not exist in Azure. Skipping import."
fi


# Import ACR password secret
# ACR_PASSWORD_SECRET_NAME="acr-admin-password"
# ACR_PASSWORD_SECRET_URI="https://$KEY_VAULT_NAME.vault.azure.net/secrets/$ACR_PASSWORD_SECRET_NAME"
# if az keyvault secret show --name "$ACR_PASSWORD_SECRET_NAME" --vault-name "$KEY_VAULT_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
#   if ! terraform state show azurerm_key_vault_secret.acr_password &>/dev/null; then
#     echo "Importing existing ACR password secret..."
#     terraform import azurerm_key_vault_secret.acr_password "$ACR_PASSWORD_SECRET_URI"
#   else
#     echo "ACR password secret already managed by Terraform. Skipping import."
#   fi
# else
#   echo "ACR password secret does not exist. Skipping import."
# fi

# Import ACR password secret
ACR_PASSWORD_SECRET_NAME="acr-admin-password"
ACR_PASSWORD_SECRET_ID=$(az keyvault secret show \
  --name "$ACR_PASSWORD_SECRET_NAME" \
  --vault-name "$KEY_VAULT_NAME" \
  --subscription "$SUBSCRIPTION_ID" \
  --query "id" -o tsv 2>/dev/null || echo "")
if [[ -n "$ACR_PASSWORD_SECRET_ID" ]]; then
  echo "ACR password secret exists in Azure."
  # Check if already managed by Terraform
  if terraform state show azurerm_key_vault_secret.acr_password &>/dev/null; then
    echo "Secret already managed by Terraform. Skipping import."
  else
    echo "Importing existing ACR password secret..."
    terraform import azurerm_key_vault_secret.acr_password "$ACR_PASSWORD_SECRET_ID"
  fi
else
  echo "ACR password secret does not exist in Azure. Skipping import."
fi


# Import blob storage connection string secret
# BLOB_CONNECTION_STRING_SECRET_NAME="blob-storage-connection-string"
# BLOB_CONNECTION_STRING_SECRET_URI="https://$KEY_VAULT_NAME.vault.azure.net/secrets/$BLOB_CONNECTION_STRING_SECRET_NAME"
# if az keyvault secret show --name "$BLOB_CONNECTION_STRING_SECRET_NAME" --vault-name "$KEY_VAULT_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
#   if ! terraform state show azurerm_key_vault_secret.blob_connection_string &>/dev/null; then
#     echo "Importing existing blob storage connection string secret..."
#     terraform import azurerm_key_vault_secret.blob_connection_string "$BLOB_CONNECTION_STRING_SECRET_URI"
#   else
#     echo "Blob storage connection string secret already managed by Terraform. Skipping import."
#   fi
# else
#   echo "Blob storage connection string secret does not exist. Skipping import."
# fi

# Import blob storage connection string secret
BLOB_CONNECTION_STRING_SECRET_NAME="blob-storage-connection-string"
BLOB_CONNECTION_STRING_SECRET_ID=$(az keyvault secret show \
  --name "$BLOB_CONNECTION_STRING_SECRET_NAME" \
  --vault-name "$KEY_VAULT_NAME" \
  --subscription "$SUBSCRIPTION_ID" \
  --query "id" -o tsv 2>/dev/null || echo "")
if [[ -n "$BLOB_CONNECTION_STRING_SECRET_ID" ]]; then
  echo "Blob storage connection string secret exists in Azure."
  # Check if already managed by Terraform
  if terraform state show azurerm_key_vault_secret.blob_connection_string &>/dev/null; then
    echo "Secret already managed by Terraform. Skipping import."
  else
    echo "Importing existing blob storage connection string secret..."
    terraform import azurerm_key_vault_secret.blob_connection_string "$BLOB_CONNECTION_STRING_SECRET_ID"
  fi
else
  echo "Blob storage connection string secret does not exist in Azure. Skipping import."
fi
