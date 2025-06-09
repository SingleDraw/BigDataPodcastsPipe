# outputs.tf - CRITICAL for GitHub Actions workflow

# ACR outputs for GitHub Actions
output "acr_login_server" {
  description = "The login server for the Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  description = "ACR admin username for GitHub Actions"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "ACR admin password for GitHub Actions"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}

# Key Vault outputs (for accessing other secrets later)
output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.kv.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.kv.vault_uri
}

# Resource Group for future deployments
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.rg.name
}

# Storage account name (might be needed for container apps)
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.storage.name
}