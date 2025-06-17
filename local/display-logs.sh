#!/bin/bash

# read --flags for this script
# Usage: ./display-logs.sh --aca_test
# This script displays logs for Azure Container Apps in the specified resource group.
set -e
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --aca_test) aca_apps_test=true ;;
        --aca_apps) aca_apps=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ -n "$aca_apps_test" ]]; then
    echo "Displaying logs for Azure Container Apps..."

    echo "Logs for whisperer-redis:"
    az containerapp logs show --name whisperer-redis \
        --resource-group rg-demo-storage # --follow --output table

    echo "Logs for redis-test:"
    az containerapp logs show --name redis-test \
        --resource-group rg-demo-storage # --follow --output table
elif [[ -n "$aca_apps" ]]; then
    echo "Displaying logs for Azure Container Apps..."

    echo "Logs for whisperer-redis:"
    az containerapp logs show --name whisperer-redis \
        --resource-group rg-demo-storage # --follow --output table

    echo "Logs for whisperer-worker:"
    az containerapp logs show --name whisperer-worker \
        --resource-group rg-demo-storage # --follow --output table
fi