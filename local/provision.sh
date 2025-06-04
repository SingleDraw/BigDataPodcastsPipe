#!/bin/bash

# ---------------------------------------------------------
# Script to trigger the GitHub Actions workflow for provisioning project setup resources:
# Resources include:
# - Azure Resource Group
# - Azure Storage Account
# - Azure Container Registry
# ---------------------------------------------------------

declare -A workflow_map=(
    [test]="azurelogin.yml"
    [bootstrap]="bootstrap.yml"
    [infra]="provision.yml"                 # Provisioning resources - triggered by bootstrap workflow too
    [images]="build-and-push-scraper.yml"
    [adf]="deploy-adf-pipeline.yml"
)

if [ "$1" != "--env" ] || [ -z "$2" ]; then
    echo "Usage: $0 --env {test|bootstrap|infra|images|adf}"
    exit 1
fi

env="$2"
workflow_file="${workflow_map[$env]}"

if [ -z "$workflow_file" ]; then
    echo "Error: Unknown environment '$env'. Valid options: ${!workflow_map[*]}"
    exit 1
fi

set -o allexport
# shellcheck disable=SC1091
source .env
set +o allexport

gh workflow run "$workflow_file" --repo "$GITHUB_REPOSITORY" 
if [ $? -ne 0 ]; then
    echo "Error: Failed to trigger the provision workflow for '$env'. Please check your permissions and try again."
    exit 1
fi
echo "Provision workflow for '$env' has been triggered successfully."