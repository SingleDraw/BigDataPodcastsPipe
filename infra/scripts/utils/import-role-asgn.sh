#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Azure Role Assignments into Terraform state
# ---------------------------------------------------------

SP_OBJECT_ID="$1"
ROLE_RESOURCE_NAME="$2"
ROLE_SCOPE="$3"
ROLE_NAME="$4"
MODULE_NAME="${5:-""}"

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <SP_OBJECT_ID> <ROLE_RESOURCE_NAME> <ROLE_SCOPE> <ROLE_NAME> [MODULE_NAME]"
  exit 1
fi

ROLE_ASSIGNMENT=$(az role assignment list --assignee "$SP_OBJECT_ID" --role "$ROLE_NAME" --scope "$ROLE_SCOPE" --query "[0].id" -o tsv)

FULL_RESOURCE_PATH="azurerm_role_assignment.$ROLE_RESOURCE_NAME"
# If MODULE_NAME is provided, prepend it to the resource name
if [[ -n "$MODULE_NAME" ]]; then
  FULL_RESOURCE_PATH="module.$MODULE_NAME.$FULL_RESOURCE_PATH"
fi

if [[ -n "$ROLE_ASSIGNMENT" ]]; then
  echo "Importing existing role assignment $ROLE_RESOURCE_NAME at $ROLE_SCOPE level..."
  terraform import "$FULL_RESOURCE_PATH" "$ROLE_ASSIGNMENT"
  echo "Role assignment $ROLE_RESOURCE_NAME at $ROLE_SCOPE imported successfully."
else
  echo "Role assignment $ROLE_RESOURCE_NAME at $ROLE_SCOPE does not exist. Skipping import."
fi