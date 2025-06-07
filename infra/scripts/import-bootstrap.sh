#!/bin/bash

set -e

# ---------------------------------------------------------
# Get the absolute path of the directory containing this script
# and set the path to the utils directory
# ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UTILS_DIR="$SCRIPT_DIR/utils"
# ---------------------------------------------------------


SUBID="$TF_VAR_subscription_id"
RGN="$TF_VAR_resource_group_name"


#----------------------------------------------------------
# Resource group
#----------------------------------------------------------
source "$UTILS_DIR/import-rg.sh" "$SUBID" "$RGN"


# ---------------------------------------------------------
# App Registration, Service Principal and Federated Identity Credential import
# ---------------------------------------------------------

APP_NAME="github-actions-app"
APP_RESOURCE_NAME="github_actions"

# Get the App ID for the GitHub Actions App Registration
# If App does not exist, it will be created
APP_ID=$(source "$UTILS_DIR/ensure-app.sh" "$APP_NAME")

if [[ -z "$APP_ID" ]]; then
  echo "Failed to retrieve or create App ID for $APP_NAME. Exiting."
  exit 1
else
  echo "App ID for $APP_NAME: $APP_ID"
fi

# Get the Service Principal object ID
SP_OBJECT_ID=$(az ad sp show --id "$APP_ID" --query "id" -o tsv)

if [[ -z "$SP_OBJECT_ID" ]]; then
  echo "Failed to retrieve Service Principal object ID for $APP_NAME. Exiting."
  exit 1
else
  echo "Service Principal object ID for $APP_NAME: $SP_OBJECT_ID"
fi

# Get the App Registration object ID
APP_OBJECT_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].id" -o tsv) 

if [[ -z "$APP_OBJECT_ID" ]]; then
  echo "Failed to retrieve App Registration object ID for $APP_NAME. Exiting."
  exit 1
else
  echo "App Registration object ID for $APP_NAME: $APP_OBJECT_ID"
fi

source "$UTILS_DIR/import-app-reg.sh" "$APP_RESOURCE_NAME" "$APP_OBJECT_ID"   # App Registration 
source "$UTILS_DIR/import-app-sp.sh" "$APP_RESOURCE_NAME" "$APP_NAME"         # App Service Principal 
source "$UTILS_DIR/import-app-fedi.sh" "$APP_RESOURCE_NAME" "$APP_OBJECT_ID"  # App Fed Id Cred 


#----------------------------------------------------------
# Role Assignments for GitHub Actions App
#----------------------------------------------------------

source "$UTILS_DIR/import-role-asgn.sh" "$SP_OBJECT_ID" \
  "github_actions_rg_contributor" \
  "/subscriptions/$SUBID/resourceGroups/$RGN" \
  "Contributor" 

source "$UTILS_DIR/import-role-asgn.sh" "$SP_OBJECT_ID" \
  "github_actions_subscription_contributor" \
  "/subscriptions/$SUBID" \
  "Contributor" 

source "$UTILS_DIR/import-role-asgn.sh" "$SP_OBJECT_ID" \
  "github_actions_user_access_administrator" \
  "/subscriptions/$SUBID" \
  "User Access Administrator"

source "$UTILS_DIR/import-role-asgn.sh" "$SP_OBJECT_ID" \
  "github_actions_role_assignment_admin" \
  "/subscriptions/$SUBID/resourceGroups/$RGN" \
  "Role Based Access Control Administrator"

source "$UTILS_DIR/import-role-asgn.sh" "$SP_OBJECT_ID" \
  "github_actions_storage_blob_data_contributor" \
  "/subscriptions/$SUBID/resourceGroups/$RGN/providers/Microsoft.Storage/storageAccounts/$TF_VAR_storage_account_name" \
  "Storage Blob Data Contributor"

#----------------------------------------------------------
# STORAGE ACCOUNT AND CONTAINERS IMPORT
#----------------------------------------------------------

STA="$TF_VAR_storage_account_name"

# Import storage account
source "$UTILS_DIR/import-st.sh" "$SUBID" "$RGN" "$STA"

# Import storage containers (tfstate, whisperer, aci-logs)
source "$UTILS_DIR/import-st-container.sh" "$SUBID" "$RGN" "$STA" "tfstate"
source "$UTILS_DIR/import-st-container.sh" "$SUBID" "$RGN" "$STA" "whisperer"
source "$UTILS_DIR/import-st-container.sh" "$SUBID" "$RGN" "$STA" "aci-logs"
