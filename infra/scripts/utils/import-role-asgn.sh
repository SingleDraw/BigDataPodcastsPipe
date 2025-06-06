#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Azure Role Assignments into Terraform state
# ---------------------------------------------------------

SP_OBJECT_ID="$1"
ROLE_RESOURCE_NAME="$2"
ROLE_SCOPE="$3"
ROLE_NAME="$4"

ROLE_ASSIGNMENT=$(az role assignment list --assignee "$SP_OBJECT_ID" --role "$ROLE_NAME" --scope "$ROLE_SCOPE" --query "[0].id" -o tsv)

if [[ -n "$ROLE_ASSIGNMENT" ]]; then
  echo "Importing existing role assignment $ROLE_RESOURCE_NAME at $ROLE_SCOPE level..."
  terraform import azurerm_role_assignment.$ROLE_RESOURCE_NAME "$ROLE_ASSIGNMENT"
else
  echo "Role assignment $ROLE_RESOURCE_NAME at $ROLE_SCOPE does not exist. Skipping import."
fi