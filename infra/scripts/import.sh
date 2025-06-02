#!/bin/bash
set -e

RESOURCE_GROUP_NAME="$TF_VAR_resource_group_name"
SUBSCRIPTION_ID="$TF_VAR_subscription_id"
RG_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"

# Check if the resource group exists
if az group show --name "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing resource group..."
  terraform import azurerm_resource_group.rg "$RG_ID"
else
  echo "Resource group does not exist. Skipping import."
fi

STORAGE_ACCOUNT_NAME="$TF_VAR_storage_account_name"
STORAGE_ACCOUNT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"
# 
Check if the storage account exists
if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing storage account..."
  terraform import azurerm_storage_account.storage "$STORAGE_ACCOUNT_ID"
else
  echo "Storage account does not exist. Skipping import."
fi

CONTAINER_REGISTRY_NAME="$TF_VAR_container_registry_name"
CONTAINER_REGISTRY_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.ContainerRegistry/registries/$CONTAINER_REGISTRY_NAME"
# Check if the container registry exists
if az acr show --name "$CONTAINER_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing container registry..."
  terraform import azurerm_container_registry.acr "$CONTAINER_REGISTRY_ID"
else
  echo "Container registry does not exist. Skipping import."
fi


KEY_VAULT_NAME="${RESOURCE_GROUP_NAME}-kv"
KEY_VAULT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"
# Check if the key vault exists
if az keyvault show --name "$KEY_VAULT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing key vault..."
  terraform import azurerm_key_vault.kv "$KEY_VAULT_ID"
else
  echo "Key vault does not exist. Skipping import."
fi


# Import secrets
# 
# 5. Store secrets in Key Vault
# resource "azurerm_key_vault_secret" "acr_username" {
#   name         = "acr-admin-username"
#   value        = azurerm_container_registry.acr.admin_username
#   key_vault_id = azurerm_key_vault.kv.id
# }

# resource "azurerm_key_vault_secret" "acr_password" {
#   name         = "acr-admin-password"
#   value        = azurerm_container_registry.acr.admin_password
#   key_vault_id = azurerm_key_vault.kv.id
# }

# resource "azurerm_key_vault_secret" "blob_connection_string" {
#   name         = "blob-storage-connection-string"
#   value        = azurerm_storage_account.storage.primary_connection_string
#   key_vault_id = azurerm_key_vault.kv.id
# }

# Import secrets
# Import ACR username secret
ACR_USERNAME_SECRET_NAME="acr-admin-username"
ACR_USERNAME_SECRET_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME/secrets/$ACR_USERNAME_SECRET_NAME"
if az keyvault secret show --name "$ACR_USERNAME_SECRET_NAME" --vault-name "$KEY_VAULT_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing ACR username secret..."
  terraform import azurerm_key_vault_secret.acr_username "$ACR_USERNAME_SECRET_ID"
else
  echo "ACR username secret does not exist. Skipping import."
fi
# Import ACR password secret
ACR_PASSWORD_SECRET_NAME="acr-admin-password"
ACR_PASSWORD_SECRET_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME/secrets/$ACR_PASSWORD_SECRET_NAME"
if az keyvault secret show --name "$ACR_PASSWORD_SECRET_NAME" --vault-name "$KEY_VAULT_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing ACR password secret..."
  terraform import azurerm_key_vault_secret.acr_password "$ACR_PASSWORD_SECRET_ID"
else
  echo "ACR password secret does not exist. Skipping import."
fi
# Import blob storage connection string secret
BLOB_CONNECTION_STRING_SECRET_NAME="blob-storage-connection-string"
BLOB_CONNECTION_STRING_SECRET_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME/secrets/$BLOB_CONNECTION_STRING_SECRET_NAME"
if az keyvault secret show --name "$BLOB_CONNECTION_STRING_SECRET_NAME" --vault-name "$KEY_VAULT_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing blob storage connection string secret..."
  terraform import azurerm_key_vault_secret.blob_connection_string "$BLOB_CONNECTION_STRING_SECRET_ID"
else
  echo "Blob storage connection string secret does not exist. Skipping import."
fi
# Import other secrets