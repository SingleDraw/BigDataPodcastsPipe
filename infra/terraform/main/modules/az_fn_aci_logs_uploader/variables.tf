variable "location" {}
variable "resource_group_name" {}
variable "function_app_name" {}
variable "service_plan_name" {
  default = "aci-fn-plan"
}
variable "storage_account_name" {}
variable "function_key" {}
variable "blob_connection_string_name" {}
variable "blob_container_name_aci_logs" {}
variable "storage_account_id" {}
variable "key_vault_id" {}
variable "key_vault_uri" {}
variable "github_oidc_sp_id" {}

variable "dependency_resources" {
  description = "List of resources that the function app depends on"
  type        = list(any)
  # This should be a list of resources that the function app depends on, e.g., Key Vault
  default     = []
}