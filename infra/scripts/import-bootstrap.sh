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

# # Check if GitHub Actions identity already exists
# IDENTITY_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.ManagedIdentity/userAssignedIdentities/github-actions-identity"
# if az identity show --name "github-actions-identity" --resource-group "$RESOURCE_GROUP_NAME" &>/dev/null; then
#   echo "Importing existing GitHub Actions identity..."
#   terraform import azurerm_user_assigned_identity.github_actions "$IDENTITY_ID"
# else
#   echo "GitHub Actions identity does not exist. Skipping import."
# fi

# # Check if Federated Identity Credential already exists
# FED_CRED_ID="$IDENTITY_ID/federatedIdentityCredentials/github-actions-oidc"
# if az identity federated-credential show --name "github-actions-oidc" --identity-name "github-actions-identity" --resource-group "$RESOURCE_GROUP_NAME" &>/dev/null; then
#   echo "Importing existing Federated Identity Credential for GitHub Actions..."
#   terraform import azurerm_federated_identity_credential.github_oidc "$FED_CRED_ID"
# else
#   echo "Federated Identity Credential for GitHub Actions does not exist. Skipping import."
# fi

# # Check if the role assignment already exists
# IDENTITY_NAME="github-actions-identity"
# if ! ASSIGNEE_OBJECT_ID=$(az identity show --name "$IDENTITY_NAME" --resource-group "$RESOURCE_GROUP_NAME" --query "principalId" -o tsv); then
#   echo "GitHub Actions identity does not exist. Skipping role assignment import."
# else
#   ROLE_NAME="Contributor"
#   SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"

#   # Check if role assignment exists
#   ASSIGNMENT_ID=$(az role assignment list \
#     --assignee "$ASSIGNEE_OBJECT_ID" \
#     --role "$ROLE_NAME" \
#     --scope "$SCOPE" \
#     --query "[0].id" -o tsv)

#   if [[ -n "$ASSIGNMENT_ID" ]]; then
#     echo "Importing existing role assignment for GitHub Actions identity..."
#     terraform import azurerm_role_assignment.github_actions_rg_contributor "$ASSIGNMENT_ID"
#   else
#     echo "Role assignment for GitHub Actions identity does not exist. Skipping import."
#   fi
# fi

# Check if GitHub Actions App Registration already exists
APP_NAME="github-actions-app"
if APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv) && [[ -n "$APP_ID" ]]; then
  echo "Importing existing GitHub Actions App Registration..."
  terraform import azuread_application.github_actions "$APP_ID"
  
  # Import the service principal
  if SP_ID=$(az ad sp list --display-name "$APP_NAME" --query "[0].id" -o tsv) && [[ -n "$SP_ID" ]]; then
    echo "Importing existing Service Principal..."
    terraform import azuread_service_principal.github_actions "$SP_ID"
  else
    echo "Service Principal does not exist. Skipping import."
  fi
  
  # Check if Federated Identity Credential already exists
  FED_CRED_NAME="github-actions-federated-credential"
  if az ad app federated-credential list --id "$APP_ID" --query "[?displayName=='$FED_CRED_NAME'].id" -o tsv | grep -q .; then
    echo "Importing existing Federated Identity Credential..."
    FED_CRED_ID=$(az ad app federated-credential list --id "$APP_ID" --query "[?displayName=='$FED_CRED_NAME'].id" -o tsv)
    terraform import azuread_application_federated_identity_credential.github_actions "$APP_ID/$FED_CRED_ID"
  else
    echo "Federated Identity Credential does not exist. Skipping import."
  fi
  
  # Check if the role assignment already exists
  if SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query "id" -o tsv); then
    ROLE_NAME="Contributor"
    SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME"

    # Check if role assignment exists
    ASSIGNMENT_ID=$(az role assignment list \
      --assignee "$SP_OBJECT_ID" \
      --role "$ROLE_NAME" \
      --scope "$SCOPE" \
      --query "[0].id" -o tsv)

    if [[ -n "$ASSIGNMENT_ID" ]]; then
      echo "Importing existing role assignment for Service Principal..."
      terraform import azurerm_role_assignment.github_actions_rg_contributor "$ASSIGNMENT_ID"
    else
      echo "Role assignment for Service Principal does not exist. Skipping import."
    fi
  fi

  # 
  # resource "azurerm_role_assignment" "github_actions_subscription_contributor" {
  #   scope                = data.azurerm_subscription.current.id
  #   role_definition_name = "Contributor"
  #   principal_id         = azuread_service_principal.github_actions.object_id
  # }

  # Import the role assignment for subscription level
  if SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query "id" -o tsv); then
    ROLE_NAME="Contributor"
    SCOPE="/subscriptions/$SUBSCRIPTION_ID"
    # Check if role assignment exists
    ASSIGNMENT_ID=$(az role assignment list \
      --assignee "$SP_OBJECT_ID" \
      --role "$ROLE_NAME" \
      --scope "$SCOPE" \
      --query "[0].id" -o tsv)

    if [[ -n "$ASSIGNMENT_ID" ]]; then
      echo "Importing existing role assignment for Service Principal at subscription level..."
      terraform import azurerm_role_assignment.github_actions_subscription_contributor "$ASSIGNMENT_ID"
    else
      echo "Role assignment for Service Principal at subscription level does not exist. Skipping import."
    fi
  fi

else
  echo "GitHub Actions App Registration does not exist. Skipping import."
fi



