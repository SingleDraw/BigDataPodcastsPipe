#!/bin/bash

az datafactory trigger-run list \
  --factory-name "rg-demo-storage-adf" \
  --resource-group "rg-demo-storage" \
  --trigger-name "DailyTrigger" \
  --start-time "$(date -u -d '-1 hour' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)"