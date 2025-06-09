# Alternative approach using local-exec provisioner
# This runs GitHub CLI commands to set secrets

resource "null_resource" "set_github_secrets" {
  # This runs after ACR is created
  depends_on = [
    azurerm_container_registry.acr,
    azurerm_key_vault.kv,
    azurerm_storage_account.storage
  ]

  provisioner "local-exec" {
    command = <<-EOT
      # Set GitHub secrets using GitHub CLI
      echo "${azurerm_container_registry.acr.login_server}" | gh secret set ACR_LOGIN_SERVER --repo ${var.github_owner}/${var.github_repository}
      echo "${azurerm_container_registry.acr.admin_username}" | gh secret set ACR_USERNAME --repo ${var.github_owner}/${var.github_repository}
      echo "${azurerm_container_registry.acr.admin_password}" | gh secret set ACR_PASSWORD --repo ${var.github_owner}/${var.github_repository}
      echo "${azurerm_resource_group.rg.name}" | gh secret set AZURE_RESOURCE_GROUP --repo ${var.github_owner}/${var.github_repository}
      echo "${azurerm_key_vault.kv.name}" | gh secret set KEY_VAULT_NAME --repo ${var.github_owner}/${var.github_repository}
      echo "${azurerm_storage_account.storage.name}" | gh secret set STORAGE_ACCOUNT_NAME --repo ${var.github_owner}/${var.github_repository}
    EOT

    environment = {
      GITHUB_TOKEN = var.github_token
    }
  }

  # Trigger re-run if any of these values change
  triggers = {
    acr_login_server = azurerm_container_registry.acr.login_server
    acr_username     = azurerm_container_registry.acr.admin_username
    acr_password     = azurerm_container_registry.acr.admin_password
    resource_group   = azurerm_resource_group.rg.name
    key_vault_name   = azurerm_key_vault.kv.name
    storage_name     = azurerm_storage_account.storage.name
  }
}