terraform {
  backend "azurerm" {}  # values provided via -backend-config in provision workflow
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 2.15.0"
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

# GitHub provider configuration
# - used for managing GitHub repositories like: storing secrets from terraform ouptuts.
provider "github" {
  token = var.github_token
  owner = var.github_owner  # Your GitHub username or organization
}
