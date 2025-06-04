
# output "aca_identity_id" {
#   value = azurerm_user_assigned_identity.aca_identity.id
# }
# output "aca_environment_id" {
#   value = azurerm_container_app_environment.aca_env.id
# }



output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}





# # and in another module, you can reference it like this:
# module "main" {
#   source = "../main"
# }

# module "job_runner" {
#   source = "./"
#   aca_environment_id        = module.main.aca_environment_id
#   aca_identity_id           = module.main.aca_identity_id
#   acr_login_server          = module.main.acr_login_server
# }



# but better solutuion is to write the outputs to github actions secrets
# 🔐 What to Store in GitHub Secrets:
# ACA_ENV_ID
# ACA_IDENTITY_ID
# ACR_LOGIN_SERVER
# AZURE_SUBSCRIPTION_ID, TENANT_ID, etc. (if not already present)
# Optional: container app name, image tag, etc.