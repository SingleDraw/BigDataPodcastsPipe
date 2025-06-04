# GitHub provider configuration
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

# Azure provider configuration
variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}
variable "location" {
    description = "Azure region for resources"
    type        = string
}
variable "resource_group_name" {
    description = "Name of the resource group"
    type        = string
}
variable "storage_account_name" {
    description = "Name of the Azure Storage Account"
    type        = string
}


