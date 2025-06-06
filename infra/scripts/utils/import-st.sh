#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Azure Storage Account into Terraform state
# ---------------------------------------------------------

SUBSCRIPTION_ID="$1"
RESOURCE_GROUP_NAME="$2"
STORAGE_ACCOUNT_NAME="$3"

STORAGE_ACCOUNT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"
# Check if the storage account exists
if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing storage account..."
  terraform import azurerm_storage_account.storage "$STORAGE_ACCOUNT_ID"
else
  echo "Storage account does not exist. Skipping import."
fi