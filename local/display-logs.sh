#!/bin/bash

echo "Displaying logs for Azure Container Apps..."

echo "Logs for whisperer-redis:"
az containerapp logs show --name whisperer-redis \
    --resource-group rg-demo-storage # --follow --output table

echo "Logs for redis-test:"
az containerapp logs show --name redis-test \
    --resource-group rg-demo-storage # --follow --output table

echo "Logs for redis-web-test:"
az containerapp logs show --name redis-web-test \
   --resource-group rg-demo-storage # --follow --output table
