#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Azure Storage Container into Terraform state
# NOTE: There is enforced naming convention for the storage container.
#       The container name must be the same as the resource name in Terraform.
#       For example, if the resource name in Terraform is "aci_logs", 
#       the container name must be at least "aci-logs".
#       This script replaces hyphens with underscores to match the Terraform resource name.
# ---------------------------------------------------------

SUBSCRIPTION_ID="$1"
RESOURCE_GROUP_NAME="$2"
STORAGE_ACCOUNT_NAME="$3"
CONTAINER_NAME="$4"

# Replace hyphens with underscores for Terraform resource name
CONTAINER_RESOURCE_NAME="${CONTAINER_NAME//-/_}"  
CONTAINER_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME/blobServices/default/containers/$CONTAINER_NAME"

# Check if the container exists using Azure CLI
if az storage container show --name "$CONTAINER_NAME" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --auth-mode login &>/dev/null; then
  echo "Importing existing storage container..."
  terraform import azurerm_storage_container.$CONTAINER_RESOURCE_NAME "$CONTAINER_ID"
else
  echo "Storage container does not exist. Skipping import."
fi