#!/bin/bash

# read --flags for this script
# Usage: ./display-logs.sh --aca_test
# This script displays logs for Azure Container Apps in the specified resource group.
set -e
while [[ "$#" -gt 0 ]]; do
    aca_apps_test=false
    aca_apps=false
    delete_whisperer=false
    case $1 in
        --aca_test) aca_apps_test=true ;;
        --aca_apps) aca_apps=true ;;
        --aca_apps_rm) delete_whisperer=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done


# DISPLAY LOGS FOR TEST CONTAINERS (redis and redis-test)
if [[ -n "$aca_apps_test" ]]; then
    echo "Displaying logs for Azure Container Apps..."

    echo "Logs for whisperer-redis:"
    az containerapp logs show --name whisperer-redis \
        --resource-group rg-demo-storage # --follow --output table

    echo "Logs for redis-test:"
    az containerapp logs show --name redis-test \
        --resource-group rg-demo-storage # --follow --output table



# DISPLAY LOGS FOR WHISPERER CONTAINERS (whisperer-redis and whisperer-worker)
elif [[ -n "$aca_apps" ]]; then
    echo "Displaying logs for Azure Container Apps..."

    echo "Logs for whisperer-redis:"
    az containerapp logs show --name whisperer-redis \
        --resource-group rg-demo-storage # --follow --output table

    echo "Logs for whisperer-worker:"
    az containerapp logs show --name whisperer-worker \
        --resource-group rg-demo-storage # --follow --output table



# DELETE WHISPERER CONTIANERS (whisperer-redis and whisperer-worker)
elif [[ -n "$delete_whisperer" ]]; then
    echo "Deleting whisperer containers..."
    az containerapp delete --name whisperer-redis \
        --resource-group rg-demo-storage --yes
    az containerapp delete --name whisperer-worker \
        --resource-group rg-demo-storage --yes


else
    echo "No valid option provided. Use --aca_test or --aca_apps."
    exit 1
fi