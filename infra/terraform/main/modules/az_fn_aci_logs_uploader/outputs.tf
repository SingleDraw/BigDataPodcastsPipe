# Linux Function App
output "function_app_id" {
  value = azurerm_linux_function_app.aci_logs_uploader.id
}

output "function_app_name" {
  value = azurerm_linux_function_app.aci_logs_uploader.name
}

output "function_app_identity_principal_id" {
  value = azurerm_linux_function_app.aci_logs_uploader.identity[0].principal_id
}

output "function_app_identity" {
  value = azurerm_linux_function_app.aci_logs_uploader.identity[0]
}

output "aci_logs_uploader_hostname" {
  value = azurerm_linux_function_app.aci_logs_uploader.default_hostname
}


# App Service Plan
output "app_service_plan_id" {
  value = azurerm_service_plan.function_plan.id
}

output "app_service_plan_name" {
  value = azurerm_service_plan.function_plan.name
}

# Role Assignments
output "role_assignment_fn_storage_id" {
  value = azurerm_role_assignment.fn_storage_role.id
}

output "role_assignment_github_id" {
  value = azurerm_role_assignment.github_deploy_rights.id
}

# Access Policy
output "key_vault_access_policy_id" {
  value = azurerm_key_vault_access_policy.fn_access.id
}


# To reference the outputs in other modules, you can use:
# 1.
# output "function_app_id" {
#   value = module.az_fn_aci_logs_uploader.function_app_id
# }
# 2.
# resource "azurem_monitor_diagnostic_setting" "example" {
#   name               = "example-diagnostic-setting"
#   target_resource_id = module.az_fn_aci_logs_uploader.function_app_id
#   ...
# }