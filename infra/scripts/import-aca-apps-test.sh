#!/bin/bash

set -e

# > Import existing Azure Container Apps resources into Terraform state

# > Data source for the Terraform variables
# ---------------------------------------------------------
SUB_ID="$TF_VAR_subscription_id"
RG_N="$TF_VAR_resource_group_name"
RG_ID="/subscriptions/$SUB_ID/resourceGroups/$RG_N"


# > Script to import existing Azure resources into Terraform state
# ----------------------------------------------------------

# 1. Import Azure Container App for Redis
CA_REDIS_N="whisperer-redis"
CA_REDIS_ID="$RG_ID/providers/Microsoft.App/containerApps/$CA_REDIS_N"
RESOURCES+=(
  "azurerm_container_app.redis|az containerapp show --name \"$CA_REDIS_N\" --resource-group \"$RG_N\"|$CA_REDIS_ID"
)

# 2. Import Azure Container App for Redis Test
CA_TEST_N="redis-test"
CA_TEST_ID="$RG_ID/providers/Microsoft.App/containerApps/$CA_TEST_N"
RESOURCES+=(
  "azurerm_container_app.redis_test|az containerapp show --name \"$CA_TEST_N\" --resource-group \"$RG_N\"|$CA_TEST_ID"
)

# > Execute the import commands for each resource
#----------------------------------------------------------
for entry in "${RESOURCES[@]}"; do
  IFS="|" read -r tf_name check_cmd res_id <<< "$entry"

  echo "Checking $tf_name..."
  if eval "$check_cmd --subscription $TF_VAR_subscription_id" &>/dev/null; then
    if terraform state show "$tf_name" &>/dev/null; then
      echo "$tf_name already managed. Skipping."
    else
      terraform import "$tf_name" "$res_id"
    fi
  else
    echo "$tf_name does not exist. Skipping."
  fi
done
