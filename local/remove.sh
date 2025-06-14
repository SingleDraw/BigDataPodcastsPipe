#!/bin/bash

# Remove all container app resources
terraform state rm 'azurerm_container_app.redis'
terraform state rm 'azurerm_container_app.worker[0]'
terraform state rm 'azurerm_container_app.worker'
terraform state rm 'azurerm_container_app.redis_test'