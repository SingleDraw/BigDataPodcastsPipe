#!/bin/bash
set -e

RESOURCE_GROUP_NAME="$TF_VAR_resource_group_name"
SUBSCRIPTION_ID="$TF_VAR_subscription_id"
# RG_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"

# # Check if the resource group exists
# if az group show --name "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
#   echo "Importing existing resource group..."
#   terraform import azurerm_resource_group.rg "$RG_ID"
# else
#   echo "Resource group does not exist. Skipping import."
# fi

# STORAGE_ACCOUNT_NAME="$TF_VAR_storage_account_name"
# STORAGE_ACCOUNT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"
# # Check if the storage account exists
# if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
#   echo "Importing existing storage account..."
#   terraform import azurerm_storage_account.storage "$STORAGE_ACCOUNT_ID"
# else
#   echo "Storage account does not exist. Skipping import."
# fi

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