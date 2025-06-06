#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Azure Application Federated Identity into Terraform state
# -----------------------------------------------------------

APP_RESOURCE_NAME="$1"
APP_OBJECT_ID="$2"

if [[ -n "$APP_OBJECT_ID" ]]; then
  FED_CRED_ID=$(az ad app federated-credential list --id "$APP_OBJECT_ID" --query "[0].id" -o tsv)
  if [[ -n "$FED_CRED_ID" && "$FED_CRED_ID" != "null" ]]; then
    echo "Importing existing Federated Identity Credential with ID: $FED_CRED_ID"
    terraform import azuread_application_federated_identity_credential.$APP_RESOURCE_NAME "$APP_OBJECT_ID/federatedIdentityCredential/$FED_CRED_ID"
  else
    echo "No federated Identity Credential found. Will create new one."
  fi
fi