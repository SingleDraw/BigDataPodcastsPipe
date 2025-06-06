#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to import existing Application Servcice Principal into Terraform state
# ---------------------------------------------------------

APP_RESOURCE_NAME="$1"
APP_NAME="$2"

SP_ID=$(az ad sp list --display-name "$APP_NAME" --query "[0].id" -o tsv)
if [[ -n "$SP_ID" ]]; then
    echo "Importing existing Service Principal..."
    terraform import azuread_service_principal.$APP_RESOURCE_NAME "$SP_ID"
else
    echo "Service Principal does not exist. Skipping import."
fi