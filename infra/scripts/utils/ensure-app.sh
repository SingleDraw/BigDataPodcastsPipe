#!/bin/bash

set -e

# ---------------------------------------------------------
# Script to ensure an Azure Application exists
# - If the application does not exist, it will be created.
# - Returns the Application ID by echoing it to stdout.
# ---------------------------------------------------------

APP_NAME="$1"

APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)

if [ -z "$APP_ID" ]; then
  echo "App not found. Creating..."
  APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
  echo "Created app with ID: $APP_ID" >&2
else
  echo "App already exists: $APP_ID" >&2
fi

echo "$APP_ID"
