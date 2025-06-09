#!/bin/bash

# Variables
RESOURCE_GROUP="your-rg"
LOCATION="eastus"
ACR_NAME="youracr"
ACA_ENV_NAME="job-processing-env"
REDIS_NAME="job-redis"

# Create Container Apps Environment
echo "Creating Container Apps Environment..."
az containerapp env create \
  --name $ACA_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create Redis Cache
echo "Creating Redis Cache..."
az redis create \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0

# Get Redis connection string
REDIS_KEY=$(az redis list-keys --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query primaryKey -o tsv)
REDIS_HOST=$(az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query hostName -o tsv)
REDIS_CONNECTION="$REDIS_HOST:6380,password=$REDIS_KEY,ssl=True"

# Create secrets in Container Apps Environment
echo "Creating secrets..."
az containerapp env secret set \
  --name $ACA_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets "redis-connection=$REDIS_CONNECTION" "storage-key=YOUR_STORAGE_KEY"

# Deploy Worker App (long-running)
echo "Deploying Worker App..."
az containerapp create \
  --name job-worker \
  --resource-group $RESOURCE_GROUP \
  --environment $ACA_ENV_NAME \
  --image $ACR_NAME.azurecr.io/job-worker:latest \
  --secrets "redis-connection=$REDIS_CONNECTION" \
  --env-vars "REDIS_URL=secretref:redis-connection" \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.5 \
  --memory 1Gi

# Create Job (submitter) - triggered on-demand
echo "Creating Job Submitter..."
az containerapp job create \
  --name job-submitter \
  --resource-group $RESOURCE_GROUP \
  --environment $ACA_ENV_NAME \
  --image $ACR_NAME.azurecr.io/job-submitter:latest \
  --secrets "redis-connection=$REDIS_CONNECTION" "storage-key=YOUR_STORAGE_KEY" \
  --env-vars "REDIS_URL=secretref:redis-connection" "STORAGE_KEY=secretref:storage-key" \
  --cpu 0.5 \
  --memory 1Gi \
  --parallelism 1 \
  --completion-count 1 \
  --restart-policy Never

echo "Deployment complete!"
echo "Redis Host: $REDIS_HOST"
echo "Container Apps Environment: $ACA_ENV_NAME"
echo ""
echo "To trigger job from ADF, use:"
echo "POST https://management.azure.com/subscriptions/SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/jobs/job-submitter/start?api-version=2023-05-01"