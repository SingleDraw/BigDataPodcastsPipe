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

variable "container_registry_name" {
    description = "Name of the Azure Container Registry"
    type        = string
}

# Custom naming for resources
variable "blob_connection_string_name" {
  description = "Name of the Azure Blob Storage connection string secret"
  type        = string
  default     = "blob-storage-connection-string"
}

variable "azure_client_id" {
  description = "Azure Client ID from GitHub secret"
  type        = string
}

# Optional if you use object_id approach
variable "azure_object_id" {
  description = "Azure Service Principal Object ID from GitHub secret"
  type        = string
}

variable "tenant_id" {
  description = "Azure Tenant ID"
  type        = string
}

# Image names for applications
variable "brick_whisperer_image_name" {
  description = "Docker image name for Whisperer App"
  type        = string
}