#!/bin/bash

# az containerapp logs show --name redis-test \
# az containerapp logs show --name redis-web-test \
az containerapp logs show --name whisperer-redis \
    --resource-group rg-demo-storage # --follow --output table
