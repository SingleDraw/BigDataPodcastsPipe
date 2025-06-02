terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 2.15.0"
    }
  }
}

provider "azurerm" {
  features {}

  # Specify Azure subscription
  subscription_id = var.subscription_id
  # tenant_id and client_id will be picked up from Azure CLI login
}

# 1. RESOURCE GROUP
import {
  to = azurerm_resource_group.rg
  id = "/subscriptions/${var.subscription_id}/resourceGroups/${var.resource_group_name}"
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# 2. STORAGE ACCOUNT

resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"  
  public_network_access_enabled   = true                                        # for access from remote machines outside azure
  allow_nested_items_to_be_public = false
  is_hns_enabled           = true                                               # Enables Data Lake Gen2 (ABFS)
}


# 3. CONTAINER REGISTRY

resource "azurerm_container_registry" "acr" {
  name                = var.container_registry_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"                                                 # cheapers option
  admin_enabled       = true                                                    # Enables username/password access
}
