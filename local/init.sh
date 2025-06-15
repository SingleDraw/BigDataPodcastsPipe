#!/bin/bash

# Force UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# read environment variables from .env file
set -o allexport
# shellcheck disable=SC1091
source .env
set +o allexport

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
if [ -z "$TF_VAR_SUBSCRIPTION_ID" ]; then
  echo "Error: Azure Subscription Id TF_VAR_SUBSCRIPTION_ID is not set as an environment variable."
  manually_set_guide_prompt
  exit 1
fi

if [ -z "$TF_VAR_GITHUB_REPOSITORY" ]; then
  echo "Error: TF_VAR_GITHUB_REPOSITORY is not set as an environment variable. It should be in the format 'owner/repo'."
  manually_set_guide_prompt
  exit 1
fi

# Check if this script is being run from GitBash on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "Running in GitBash or Cygwin environment."
    # set alias for az command to az.cmd
    alias az=az.cmd
    SCOPES="\/subscriptions\/$TF_VAR_SUBSCRIPTION_ID"
else
    echo "Running in a Unix-like environment."
    SCOPES="/subscriptions/$TF_VAR_SUBSCRIPTION_ID"
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
# echo "Setting GitHub secret AZURE_CREDENTIALS..."
# gh secret set AZURE_CREDENTIALS \
#     --body "$(create_service_principal)" \
#     --repo "$TF_VAR_GITHUB_REPOSITORY" 
echo "Creating service principal and setting GitHub secret..."

CREDENTIALS_JSON=$(create_service_principal)

# Extract the JSON output and set it as a GitHub secret
if [ $? -ne 0 ]; then
    echo "Error: Failed to create service principal. Please check your Azure permissions and try again."
    exit 1
fi
# Extract JSON clientId, clientSecret, tenantId, and subscriptionId without using jq
if [[ -z "$CREDENTIALS_JSON" ]]; then
    echo "Error: Failed to create service principal. The output is empty."
    exit 1
fi
# validate JSON format
if ! echo "$CREDENTIALS_JSON" | grep -q '"clientId"\s*:\s*"[^"]\+"'; then
    echo "Error: The output is not in the expected JSON format. Please check the service principal creation command."
    exit 1
fi

# Extract the values from the JSON output and set them as GitHub secrets

# Subscription ID
gh secret set AZURE_SUBSCRIPTION_ID \
    --body "$TF_VAR_SUBSCRIPTION_ID" \
    --repo "$TF_VAR_GITHUB_REPOSITORY"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set GitHub secret AZURE_SUBSCRIPTION_ID."
    exit 1
fi

# Client ID - dont store it as a secret, it is not sensitive
CLIENT_ID=$(echo "$CREDENTIALS_JSON" | grep -oP '"clientId"\s*:\s*"\K[^"]+')

# Tenant ID
gh secret set AZURE_TENANT_ID \
    --body "$(echo "$CREDENTIALS_JSON" | grep -oP '"tenantId"\s*:\s*"\K[^"]+')" \
    --repo "$TF_VAR_GITHUB_REPOSITORY"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set GitHub secret AZURE_TENANT_ID."
    exit 1
fi

# Client Secret
gh secret set AZURE_CLIENT_SECRET \
    --body "$(echo "$CREDENTIALS_JSON" | grep -oP '"clientSecret"\s*:\s*"\K[^"]+')" \
    --repo "$TF_VAR_GITHUB_REPOSITORY"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set GitHub secret AZURE_CLIENT_SECRET."
    exit 1
fi

# Set credentials JSON as a GitHub secret
gh secret set AZURE_CREDENTIALS \
    --body "$CREDENTIALS_JSON" \
    --repo "$TF_VAR_GITHUB_REPOSITORY"

# check if the role already exists
ROLE_EXISTS=$(az role definition list --name "User Access Administrator" --query "[].name" -o tsv)

if [[ -z "$ROLE_EXISTS" ]]; then
    echo "Assigning 'User Access Administrator' role to the service principal..."
    az role assignment create \
        --assignee "$CLIENT_ID" \
        --role "User Access Administrator" \
        --scope "$SCOPES"

    if [ $? -ne 0 ]; then
        echo "Error: Failed to assign 'User Access Administrator' role."
        manually_set_guide_prompt
        exit 1
    fi
    echo "Role 'User Access Administrator' has been assigned to the service principal successfully."
else
    echo "Role 'User Access Administrator' already exists for the service principal. Skipping role assignment."
fi

echo "GitHub secret AZURE_CREDENTIALS has been set successfully."

# Set other secrets
AZURE_SECRETS=(
    TF_VAR_RESOURCE_GROUP_NAME      
    TF_VAR_LOCATION                 
    TF_VAR_STORAGE_ACCOUNT_NAME     
    TF_VAR_CONTAINER_REGISTRY_NAME
    TF_VAR_SUBSCRIPTION_ID
    TF_VAR_GITHUB_OWNER
    TF_VAR_GITHUB_REPOSITORY
    GH_PAT_TOKEN
    PODCASTING_INDEX_API_KEY
    PODCASTING_INDEX_API_SECRET
    BRICK_PCASTER_IMAGE_NAME
    BRICK_ENRICHER_IMAGE_NAME
    BRICK_WHISPERER_IMAGE_NAME
    TF_VAR_FUNCTION_KEY
    TF_VAR_FUNCTION_APP_NAME
)
#   TF_VAR_CONTAINER_APP_ENVIRONMENT_NAME  
#    TF_VAR_CONTAINER_GROUP_NAME

for secret in "${AZURE_SECRETS[@]}"; do
    echo "Setting GitHub secret $secret..."
    gh secret set "$secret" \
        --body "${!secret}" \
        --repo "$TF_VAR_GITHUB_REPOSITORY"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to set GitHub secret $secret. Please check your permissions and try again."
        manually_set_guide_prompt
        exit 1
    fi
    echo "GitHub secret $secret has been set successfully."
done

# Create the infra-ready environment
if [ -z "$TF_VAR_GITHUB_OWNER" ]; then
    echo "Error: TF_VAR_GITHUB_OWNER is not set as an environment variable."
    manually_set_guide_prompt
    exit 1
fi
if [ -z "$TF_VAR_GITHUB_REPOSITORY" ]; then
    echo "Error: TF_VAR_GITHUB_REPOSITORY is not set as an environment variable."
    manually_set_guide_prompt
    exit 1
fi
echo "Creating the 'infra-ready' environment in GitHub repository '$TF_VAR_GITHUB_REPOSITORY'..."

gh api \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  repos/$TF_VAR_GITHUB_REPOSITORY/environments/infra-ready


if [ $? -ne 0 ]; then
    echo "Error: Failed to create the 'infra-ready' environment. Please check your permissions and try again."
    exit 1
fi

gh variable set INFRA_READY --env infra-ready --body "false"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set the INFRA_READY variable in the 'infra-ready' environment. Please check your permissions and try again."
    exit 1
fi

echo "Environment 'infra-ready' has been created successfully."

