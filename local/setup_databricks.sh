#!/bin/bash

az network vnet subnet show \
  --resource-group rg-demo-storage \
  --vnet-name aca-vnet \
  --name aca-subnet \
  --query "delegations"




# az config set extension.use_dynamic_install=yes_without_prompt
# az config set extension.use_dynamic_install_allow_preview=true

# # Get the workspace URL
# WORKSPACE_URL=$(az databricks workspace show \
#   --name nlp-workspace \
#   --resource-group rg \
#   --query workspaceUrl -o tsv)


# if [ -z "$WORKSPACE_URL" ]; then
#   echo "Error: Unable to retrieve the Databricks workspace URL. Please check if the workspace exists."
#   exit 1
# fi
# echo "Databricks workspace URL: $WORKSPACE_URL"












# # Log in to Databricks
# DATABRICKS_HOST="https://${WORKSPACE_URL}"
# az extension add --name databricks

# # Grant your user or SP the Workspace Admin role
# az databricks workspace-permission create \
#   --workspace-name nlp-workspace \
#   --resource-group rg \
#   --access-control-levels "WorkspaceAdmin" \
#   --principal <your-user-or-app-name>
