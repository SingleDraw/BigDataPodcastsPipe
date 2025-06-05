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
# Check if the storage account exists
if az storage account show --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --subscription "$SUBSCRIPTION_ID" &>/dev/null; then
  echo "Importing existing storage account..."
  terraform import azurerm_storage_account.storage "$STORAGE_ACCOUNT_ID"
else
  echo "Storage account does not exist. Skipping import."
fi




# Import storage container (tfstate)
CONTAINER_NAME="tfstate"
CONTAINER_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME/blobServices/default/containers/$CONTAINER_NAME"

# Check if the container exists using Azure CLI
if az storage container show --name "$CONTAINER_NAME" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --auth-mode login &>/dev/null; then
  echo "Importing existing storage container..."
  terraform import azurerm_storage_container.tfstate "$CONTAINER_ID"
else
  echo "Storage container does not exist. Skipping import."
fi

# Import storage container (tfstate)
CONTAINER_NAME="whisperer"
CONTAINER_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME/blobServices/default/containers/$CONTAINER_NAME"

# Check if the container exists using Azure CLI
if az storage container show --name "$CONTAINER_NAME" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --auth-mode login &>/dev/null; then
  echo "Importing existing storage container..."
  terraform import azurerm_storage_container.whisperer "$CONTAINER_ID"
else
  echo "Storage container does not exist. Skipping import."
fi


# Import storage container (aci-logs)
CONTAINER_NAME="aci-logs"
CONTAINER_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME/blobServices/default/containers/$CONTAINER_NAME"

# Check if the container exists using Azure CLI
if az storage container show --name "$CONTAINER_NAME" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --auth-mode login &>/dev/null; then
  echo "Importing existing storage container..."
  terraform import azurerm_storage_container.aci_logs "$CONTAINER_ID"
else
  echo "Storage container does not exist. Skipping import."
fi


# Github Actions OIDC identity

# Check if GitHub Actions identity already exists
IDENTITY_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.ManagedIdentity/userAssignedIdentities/github-actions-identity"
if az identity show --name "github-actions-identity" --resource-group "$RESOURCE_GROUP_NAME" &>/dev/null; then
  echo "Importing existing GitHub Actions identity..."
  terraform import azurerm_user_assigned_identity.github_actions "$IDENTITY_ID"
else
  echo "GitHub Actions identity does not exist. Skipping import."
fi

# Check if Federated Identity Credential already exists
FED_CRED_ID="$IDENTITY_ID/federatedIdentityCredentials/github-actions-oidc"
if az identity federated-credential show --name "github-actions-oidc" --identity-name "github-actions-identity" --resource-group "$RESOURCE_GROUP_NAME" &>/dev/null; then
  echo "Importing existing Federated Identity Credential for GitHub Actions..."
  terraform import azurerm_federated_identity_credential.github_oidc "$FED_CRED_ID"
else
  echo "Federated Identity Credential for GitHub Actions does not exist. Skipping import."
fi


# Contributor role for the specific resource group
# resource "azurerm_role_assignment" "github_actions_rg_contributor" {
#   scope                = azurerm_resource_group.rg.id
#   role_definition_name = "Contributor"
#   principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
# }
