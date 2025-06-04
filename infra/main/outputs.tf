
# output "aca_identity_id" {
#   value = azurerm_user_assigned_identity.aca_identity.id
# }
# output "aca_environment_id" {
#   value = azurerm_container_app_environment.aca_env.id
# }

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

# output "aci_identity_id" {
#   value = azurerm_user_assigned_identity.storage_identity.client_id
# }
