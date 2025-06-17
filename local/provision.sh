#!/bin/bash

# Provision script for GitHub Actions workflows
# This script triggers the appropriate GitHub Actions workflow based on the provided environment.
# Usage: ./provision.sh --env {test|bootstrap|infra|images|adf|pipetest|azfnlogs|cleanacr|image_scraper|image_enricher|image_whisperer|buildtest}
# 

TAG_MODE="latest" # Default tag mode for build and push workflows

# Map for GitHub Actions workflows
declare -A workflow_map=(
    [test]="azurelogin.yml"                                   # -- Login to Azure - test workflow  
    [cleanacr]="utils.clean-acr-registry.yml"                 # -- Clean up Azure Container Registry
    [bootstrap]="bootstrap.yml"             # Bootstrap workflow - creates the initial setup    
    [infra]="provision.yml"                 # Provisioning resources - triggered by bootstrap workflow too
    [adf]="deploy-adf-pipeline.yml"         # Deploy Azure Data Factory pipeline    
    [pipetest]="deploy-adf-pipetest.yml"        # -- Deploy ADF pipeline for test
    [azfnlogs]="deploy-az-fn-logs-uploader.yml" # Deploy Azure Function for logs uploader
    [aca_env]="provision-aca-env.yml"         # Provision Azure Container Apps environment
)

# Map for build and push workflows - these use tagMode flag
# to specify the tag mode for the images being built and pushed.
declare -A builders_map=(
    [image_scraper]="build-and-push-scraper.yml"   # Build and push scraper image  
    [image_enricher]="build-and-push-enricher.yml" # Build and push enricher image
    [image_whisperer]="build-and-push-whisperer.yml" # Build and push whisperer image
    [buildtest]="build-and-push-test.yml"       # -- Build and push test image
)

if [ "$1" != "--env" ] || [ -z "$2" ]; then
    echo "Usage: $0 --env {test|bootstrap|infra|images|adf}"
    exit 1
fi

env="$2"
workflow_file="${workflow_map[$env]}"
builder_file="${builders_map[$env]}"

if [ -z "$workflow_file" ] && [ -z "$builder_file" ]; then
    echo "Error: Unknown environment '$env'. Valid options: ${!workflow_map[*]} or ${!builders_map[*]}"
    exit 1
fi

set -o allexport
# shellcheck disable=SC1091
source .env
set +o allexport

# Run the GitHub Actions workflow
running_workflow="${workflow_file:-$builder_file}"
echo "Triggering GitHub Actions workflow '$running_workflow' for environment '$env'..."

if [ -n "$workflow_file" ]; then
    gh workflow run "$workflow_file" \
        --repo "$GITHUB_REPOSITORY"
elif [ -n "$builder_file" ]; then
    gh workflow run "$builder_file" \
        --repo "$GITHUB_REPOSITORY" \
        -f tagMode="$TAG_MODE"
else
    echo "Error: No workflow file found for environment '$env'."
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "Error: Failed to trigger the provision workflow for '$env'. Please check your permissions and try again."
    exit 1
fi
echo "Provision workflow for '$env' has been triggered successfully."