#!/bin/bash

# Debugging terraform import script for GitHub Actions App Registration and Service Principal

# ---------------------------------------------------------
# Script to import existing GitHub Actions App Registration and Service Principal into Terraform state
# ---------------------------------------------------------
az ad app list --display-name "github-actions-app" -o table


APP_NAME="github-actions-app"
APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)

# APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].id" -o tsv)

if [[ -z "$APP_ID" ]]; then
  echo "Error: GitHub Actions App Registration '$APP_NAME' not found."
  exit 1
fi

echo "Importing existing GitHub Actions App Registration..."

echo "App ID: $APP_ID"
# terraform import azuread_application.github_actions "/applications/$APP_ID"


SP_ID=$(az ad sp list --display-name "$APP_NAME" --query "[0].id" -o tsv)
if [[ -z "$SP_ID" ]]; then
  echo "Error: Service Principal for '$APP_NAME' not found."
  exit 1
fi

echo "Importing existing Service Principal..."

echo "Service Principal ID: $SP_ID"
# terraform import azuread_service_principal.github_actions "$SP_ID"


# ---

# github cheatsheet
gh run list
gh run cancel 15473921372 # cancel a run ID
gh run cancel 15474012031 

gh api /rate_limit
https://github.com/settings/billing

# check for stuck runs
gh run list --limit 10
