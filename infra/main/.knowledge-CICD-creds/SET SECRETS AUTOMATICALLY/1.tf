# terraform/providers.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# GitHub provider configuration
provider "github" {
  token = var.github_token
  owner = var.github_owner  # Your GitHub username or org
}

# terraform/variables.tf
variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub owner (username or organization)"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository name"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

# terraform/main.tf - Your existing resources
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = "East US"
}

resource "azurerm_container_registry" "acr" {
  name                = "${var.resource_group_name}acr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = true
}

resource "azurerm_storage_account" "storage" {
  name                     = "${var.resource_group_name}storage"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_key_vault" "kv" {
  name                = "${var.resource_group_name}-kv"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    secret_permissions = [
      "Get", "List", "Set", "Delete"
    ]
  }
}

# Store secrets in Key Vault
resource "azurerm_key_vault_secret" "acr_username" {
  name         = "acr-admin-username"
  value        = azurerm_container_registry.acr.admin_username
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "acr_password" {
  name         = "acr-admin-password"
  value        = azurerm_container_registry.acr.admin_password
  key_vault_id = azurerm_key_vault.kv.id
}

resource "azurerm_key_vault_secret" "blob_connection_string" {
  name         = "blob-storage-connection-string"
  value        = azurerm_storage_account.storage.primary_connection_string
  key_vault_id = azurerm_key_vault.kv.id
}

# AUTOMATICALLY SET GITHUB SECRETS
resource "github_actions_secret" "acr_login_server" {
  repository      = var.github_repository
  secret_name     = "ACR_LOGIN_SERVER"
  plaintext_value = azurerm_container_registry.acr.login_server
}

resource "github_actions_secret" "acr_username" {
  repository      = var.github_repository
  secret_name     = "ACR_USERNAME"
  plaintext_value = azurerm_container_registry.acr.admin_username
}

resource "github_actions_secret" "acr_password" {
  repository      = var.github_repository
  secret_name     = "ACR_PASSWORD"
  plaintext_value = azurerm_container_registry.acr.admin_password
}

resource "github_actions_secret" "resource_group_name" {
  repository      = var.github_repository
  secret_name     = "AZURE_RESOURCE_GROUP"
  plaintext_value = azurerm_resource_group.rg.name
}

resource "github_actions_secret" "key_vault_name" {
  repository      = var.github_repository
  secret_name     = "KEY_VAULT_NAME"
  plaintext_value = azurerm_key_vault.kv.name
}

resource "github_actions_secret" "storage_account_name" {
  repository      = var.github_repository
  secret_name     = "STORAGE_ACCOUNT_NAME"
  plaintext_value = azurerm_storage_account.storage.name
}

data "azurerm_client_config" "current" {}