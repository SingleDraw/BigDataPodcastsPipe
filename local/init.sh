#!/bin/bash

# Force UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# read environment variables from .env file
set -o allexport
# shellcheck disable=SC1091
source .env
set +o allexport

function create_json_credentials() {
    # Creates a JSON object with the required fields for GitHub Actions
    # to authenticate with Azure.
    echo "Creating JSON credentials for GitHub Actions..."
    az ad sp create-for-rbac \
        --name "gha-terraform" \
        --role "Contributor" \
        --scopes "$SCOPES" \
        --sdk-auth \
        --output json > azure-credentials.json
}

function create_service_principal() {
    az ad sp create-for-rbac \
        --name "gha-terraform" \
        --role "Contributor" \
        --scopes "$SCOPES" \
        --sdk-auth
}

function manually_set_guide_prompt() {
    echo "To manually set the GitHub secret AZURE_CREDENTIALS, follow these steps:"
    echo "Log in to your GitHub account."
    echo "Navigate to the repository settings."
    echo "Go to the 'Secrets and variables' section."
    echo "Click on 'Actions' and then 'New repository secret'."
    echo "Set the name as 'AZURE_CREDENTIALS' and paste the JSON output from the service principal creation command."
    echo "Click 'Add secret' to save it."
    echo "Credentials syntax:"
    echo "  {\"clientId\": \"<appId>\", \"clientSecret\": \"<password>\", \"tenantId\": \"<tenant>\", \"subscriptionId\": \"<subscriptionId>\"}"
}


# Check if AZURE_SUBSCRIPTION_ID is set
if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
  echo "Error: AZURE_SUBSCRIPTION_ID is not set as an environment variable."
  manually_set_guide_prompt
  exit 1
fi

if [ -z "$GITHUB_REPOSITORY" ]; then
  echo "Error: GITHUB_REPOSITORY is not set as an environment variable. It should be in the format 'owner/repo'."
  manually_set_guide_prompt
  exit 1
fi

# Check if this script is being run from GitBash on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "Running in GitBash or Cygwin environment."
    # set alias for az command to az.cmd
    alias az=az.cmd
    SCOPES="\/subscriptions\/$AZURE_SUBSCRIPTION_ID"
else
    echo "Running in a Unix-like environment."
    SCOPES="/subscriptions/$AZURE_SUBSCRIPTION_ID"
fi


# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed. Please install it and try again."
    manually_set_guide_prompt
    exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI is not installed. Please install it and try again."
    manually_set_guide_prompt
    exit 1
fi

# Check if the user is logged in to Azure
if ! az account show &> /dev/null; then
    echo "Error: You are not logged in to Azure. Please log in using 'az login' and try again."
    manually_set_guide_prompt
    exit 1
fi

# Check if the user is logged in to GitHub
if ! gh auth status &> /dev/null; then
    echo "Error: You are not logged in to GitHub. Please log in using 'gh auth login' and try again."
    manually_set_guide_prompt
    exit 1
fi

echo "All prerequisites are met. Proceeding with service principal creation..."

# Create the service principal and set it as a GitHub secret
echo "Setting GitHub secret AZURE_CREDENTIALS..."
gh secret set AZURE_CREDENTIALS \
    --body "$(create_service_principal)" \
    --repo "$GITHUB_REPOSITORY" 

if [ $? -ne 0 ]; then
    echo "Error: Failed to set GitHub secret AZURE_CREDENTIALS. Please check your permissions and try again."
    manually_set_guide_prompt
    exit 1
fi

echo "GitHub secret AZURE_CREDENTIALS has been set successfully."

# Set other secrets
AZURE_SECRETS=(
    TF_VAR_RESOURCE_GROUP_NAME      
    TF_VAR_LOCATION                 
    TF_VAR_STORAGE_ACCOUNT_NAME     
    TF_VAR_SUBSCRIPTION_ID
    TF_VAR_GITHUB_OWNER
    TF_VAR_GITHUB_REPOSITORY
    GH_PAT_TOKEN
)
#   TF_VAR_CONTAINER_REGISTRY_NAME  
#   TF_VAR_CONTAINER_APP_ENVIRONMENT_NAME  

for secret in "${AZURE_SECRETS[@]}"; do
    echo "Setting GitHub secret $secret..."
    gh secret set "$secret" \
        --body "${!secret}" \
        --repo "$GITHUB_REPOSITORY"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to set GitHub secret $secret. Please check your permissions and try again."
        manually_set_guide_prompt
        exit 1
    fi
    echo "GitHub secret $secret has been set successfully."
done
