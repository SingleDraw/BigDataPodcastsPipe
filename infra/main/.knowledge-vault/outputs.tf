# outputs.tf - Optional file for exposing values
# Useful when you need to reference these values in other Terraform configurations

output "key_vault_uri" {
  description = "The URI of the Key Vault"
  value       = azurerm_key_vault.kv.vault_uri
}

output "key_vault_id" {
  description = "The ID of the Key Vault"
  value       = azurerm_key_vault.kv.id
}

output "acr_login_server" {
  description = "The login server for the Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

# Sensitive outputs (won't be displayed in CLI output)
output "acr_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

# Note: Don't output the password directly - it's already in Key Vault