#!/bin/bash

set -a
# shellcheck disable=SC1091
source .env
set +a

# Set the Podcasting Index API secret
# Due to dollar sign in the secret, we need to escape it
if [ -z "$PODCASTING_INDEX_API_SECRET" ]; then
    echo "Error: PODCASTING_INDEX_API_KEY is not set. Please set it before running this script."
    exit 1
fi

gh secret set PODCASTING_INDEX_API_SECRET \
    --body "$PODCASTING_INDEX_API_SECRET" \
    --repo "$TF_VAR_GITHUB_REPOSITORY"

if [ $? -ne 0 ]; then
    echo "Error: Failed to set the PODCASTING_INDEX_API_SECRET secret. Please check your permissions and try again."
    exit 1
fi
echo "PODCASTING_INDEX_API_SECRET has been set successfully."