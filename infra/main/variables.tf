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
variable "blob_container_name_aci_logs" {
  description = "Name of the Azure Blob Storage container for ACI logs"
  type        = string
  default     = "aci-logs"
}

# Podcasting Index API configuration
variable "podcasting_index_api_key" {
  description = "API key for Podcasting Index"
  type        = string
  sensitive   = true
}

variable "podcasting_index_api_secret" {
  description = "API secret for Podcasting Index"
  type        = string
  sensitive   = true
}

# Image names for container apps
variable "brick_pcaster_image_name" {
  description = "Docker image name for PCaster Scraper App"
  type        = string
}




# variable "container_group_name" {
#     description = "Name of the Azure Container Group for PCaster Scraper App"
#     type        = string
# }

# variable "container_app_environment_name" {
#     description = "Name of the Azure Container App Environment"
#     type        = string
# }
