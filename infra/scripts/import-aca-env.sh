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

# 1. Import Azure Virtual Network for ACA Subnet
VNET_N="aca-vnet"
VNET_ID="$RG_ID/providers/Microsoft.Network/virtualNetworks/$VNET_N"
RESOURCES+=(
  "azurerm_virtual_network.vnet|az network vnet show --name \"$VNET_N\" --resource-group \"$RG_N\"|$VNET_ID"
)

# 2. Import Azure Subnet for Azure Container Apps
SUBNET_N="aca-subnet"
SUBNET_ID="$RG_ID/providers/Microsoft.Network/virtualNetworks/$VNET_N/subnets/$SUBNET_N"
RESOURCES+=(
  "azurerm_subnet.aca_subnet|az network vnet subnet show --name \"$SUBNET_N\" --resource-group \"$RG_N\" --vnet-name \"$VNET_N\"|$SUBNET_ID"
)

# 3. Import ACA environment
ACA_ENV_N="whisperer-aca-env"
ACA_ENV_ID="$RG_ID/providers/Microsoft.App/managedEnvironments/$ACA_ENV_N"
RESOURCES+=(
  "azurerm_container_app_environment.aca_env|az containerapp env show --name \"$ACA_ENV_N\" --resource-group \"$RG_N\"|$ACA_ENV_ID"
)

# 4. Import user-assigned managed identity for ACA
ACA_IDENTITY_N="whisperer-aca-identity"
ACA_IDENTITY_ID="$RG_ID/providers/Microsoft.ManagedIdentity/userAssignedIdentities/$ACA_IDENTITY_N"
RESOURCES+=(
  "azurerm_user_assigned_identity.aca_identity|az identity show --name \"$ACA_IDENTITY_N\" --resource-group \"$RG_N\"|$ACA_IDENTITY_ID"
)
# 5. Import role assignment for ACR Pull
ACR_PULL_ROLE_N="${RG_N}-aca-identity-acr-pull"
ACR_PULL_ROLE_ID="$RG_ID/providers/Microsoft.ContainerRegistry/registries/$CR_N/providers/Microsoft.Authorization/roleAssignments/$ACR_PULL_ROLE_N"
RESOURCES+=(
  "azurerm_role_assignment.aca_identity_acr_pull|az role assignment show --name \"$ACR_PULL_ROLE_N\" --scope \"/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.ContainerRegistry/registries/$CR_N\"|\"$ACR_PULL_ROLE_ID\""
)

# 6. Import role assignment for Network Contributor
NETWORK_ROLE_N="${RG_N}-aca-identity-network"
NETWORK_ROLE_ID="$RG_ID/providers/Microsoft.Network/virtualNetworks/$VNET_N/providers/Microsoft.Authorization/roleAssignments/$NETWORK_ROLE_N"
RESOURCES+=(
  "azurerm_role_assignment.aca_identity_network|az role assignment show --name \"$NETWORK_ROLE_N\" --scope \"/subscriptions/$SUB_ID/resourceGroups/$RG_N/providers/Microsoft.Network/virtualNetworks/$VNET_N\"|\"$NETWORK_ROLE_ID\""
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
