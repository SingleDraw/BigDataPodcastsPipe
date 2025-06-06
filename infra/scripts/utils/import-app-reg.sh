#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Application Registration (Azure AD App) into Terraform state
# - it makes sure the app exists, otherwise it creates it
# - this makes the app (used by GH Actions) manageble by Terraform
# ---------------------------------------------------------
# github-actions-app (Azure AD App Registration) - terraform: azuread_application.github_actions
# │
# ├── Service Principal - terraform: azuread_service_principal.github_actions
# │   │
# │   ├── Role Assignment at Resource Group level - terraform: azurerm_role_assignment.github_actions_rg_contributor
# │   │     Scope: /subscriptions/$SUBID/resourceGroups/$RGN
# │   │     
# │   └── Role Assignment at Subscription level - terraform: azurerm_role_assignment.github_actions_subscription_contributor
# │         Scope: /subscriptions/$SUBID
# │
# └── Federated Identity Credential - terraform: azuread_application_federated_identity_credential.github_actions
#       ID: $APP_OBJECT_ID/federatedIdentityCredential/$FED_CRED_ID
# ---------------------------------------------------------

APP_RESOURCE_NAME="$1"
APP_OBJECT_ID="$2"

if [[  -n "$APP_RESOURCE_NAME" && -n "$APP_OBJECT_ID" ]]; then
  echo "Importing existing GitHub Actions App Registration..."
  terraform import azuread_application.$APP_RESOURCE_NAME "/applications/$APP_OBJECT_ID"
else
  echo "GitHub Actions App Registration does not exist. Skipping import."
fi