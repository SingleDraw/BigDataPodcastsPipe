terraform {
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
  # All authentication details will be picked up from Azure CLI login
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}
