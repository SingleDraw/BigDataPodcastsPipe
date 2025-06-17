
#----------------------------------------------------------------------------------
# Load data sources for existing Azure resources
#----------------------------------------------------------------------------------

# 1. Azure Resource Group
data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

# 2. Azure Storage Account
data "azurerm_storage_account" "storage" {
  name                = var.storage_account_name
  resource_group_name = data.azurerm_resource_group.rg.name
}

# 3. ACR - Azure Container Registry
data "azurerm_container_registry" "acr" {
  name                = var.container_registry_name
  resource_group_name = data.azurerm_resource_group.rg.name
}

# 4. Azure Client Configuration
data "azurerm_client_config" "current" {}

# 5. Azure AD Service Principal for GitHub OIDC
data "azuread_service_principal" "github_oidc" {
  client_id = var.azure_client_id
}

# 6. KV - Azure Key Vault
data "azurerm_key_vault" "kv" {
  name                = "${var.resource_group_name}-kv"
  resource_group_name = data.azurerm_resource_group.rg.name
}

# Store ACR credentials in Key Vault
data "azurerm_key_vault_secret" "acr_username" {
  name         = "acr-admin-username"
  key_vault_id = data.azurerm_key_vault.kv.id
}

data "azurerm_key_vault_secret" "acr_password" {
  name         = "acr-admin-password"
  key_vault_id = data.azurerm_key_vault.kv.id
}

# Store storage connection string
data "azurerm_key_vault_secret" "blob_connection_string" {
  name         = var.blob_connection_string_name
  key_vault_id = data.azurerm_key_vault.kv.id
}


#----------------------------------------------------------------------------------
# Manage new Azure resources for the BigDataPipe project
#----------------------------------------------------------------------------------

# 1. Create Azure Virtual Network for ACA Subnet 🌐
resource "azurerm_virtual_network" "vnet" {
  name                = "aca-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
}

# 2. Create Azure Subnet for ACA 🕸️
resource "azurerm_subnet" "aca_subnet" {
  name                 = "aca-subnet"
  resource_group_name  = data.azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.0.0/23"]

  # Delegate the subnet to Azure Container Apps service
  delegation {
    name = "acaDelegation"

    service_delegation {
      name = "Microsoft.App/environments"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}

# 3. Create ACA environment for Big Data Processing 🌍
resource "azurerm_container_app_environment" "aca_env" {
  name                = "whisperer-aca-env"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name

  # This configuration will automatically handle the subnet delegation
  internal_load_balancer_enabled  = true
  infrastructure_subnet_id        = azurerm_subnet.aca_subnet.id
}

# 4. Create user-assigned managed identity for ACA 🧑‍💼
resource "azurerm_user_assigned_identity" "aca_identity" {
  name                = "whisperer-aca-identity"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location

  depends_on = [
    azurerm_container_app_environment.aca_env
  ]
}

# Assign AcrPull role to managed identity 🎖️
resource "azurerm_role_assignment" "aca_identity_acr_pull" {
  scope                = data.azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aca_identity.principal_id

  depends_on = [
    azurerm_user_assigned_identity.aca_identity,
    azurerm_container_app_environment.aca_env
  ]
}

# Assign Network Contributor role to managed identity for VNet access 🎖️
resource "azurerm_role_assignment" "aca_identity_network" {
  scope                = azurerm_virtual_network.vnet.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.aca_identity.principal_id

  depends_on = [
    azurerm_user_assigned_identity.aca_identity,
    azurerm_virtual_network.vnet
  ]
}