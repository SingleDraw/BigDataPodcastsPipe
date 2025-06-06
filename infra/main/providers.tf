terraform {
  backend "azurerm" {}  # values provided via -backend-config in provision workflow
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 2.15.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "azurerm" {
  features {}

  # Specify Azure subscription
  subscription_id = var.subscription_id
  # tenant_id and client_id will be picked up from Azure CLI login
}

provider "azuread" {
  # Will use the same authentication as azurerm (OIDC in your case)
  tenant_id = var.tenant_id  # Add this variable
}

# GitHub provider configuration
# - used for managing GitHub repositories like: storing secrets from terraform ouptuts.
provider "github" {
  token = var.github_token
  owner = var.github_owner  # Your GitHub username or organization
}
