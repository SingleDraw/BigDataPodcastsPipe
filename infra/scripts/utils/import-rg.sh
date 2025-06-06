#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Azure Resource Group into Terraform state
# ---------------------------------------------------------


SUBSCRIPTION_ID="$1"
RESOURCE_GROUP_NAME="$2"


RG_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"

# Check if the resource group exists
if az group show --name "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing resource group..."
  terraform import azurerm_resource_group.rg "$RG_ID"
else
  echo "Resource group does not exist. Skipping import."
fi