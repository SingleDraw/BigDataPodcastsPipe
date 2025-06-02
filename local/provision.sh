#!/bin/bash

# ---------------------------------------------------------
# Script to trigger the GitHub Actions workflow for provisioning project setup resources:
# Resources include:
# - Azure Resource Group
# - Azure Storage Account
# - Azure Container Registry
# ---------------------------------------------------------

set -o allexport
# shellcheck disable=SC1091
source .env
set +o allexport

gh workflow run provision.yml --repo "$GITHUB_REPOSITORY" 
if [ $? -ne 0 ]; then
    echo "Error: Failed to trigger the provision workflow. Please check your permissions and try again."
    exit 1
fi
echo "Provision workflow has been triggered successfully."