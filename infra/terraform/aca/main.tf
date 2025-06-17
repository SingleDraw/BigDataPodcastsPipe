
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
        "Microsoft.Network/virtualNetworks/subnets/action"
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



# 1. ACA - Azure Container Apps for Big Data Processing
# # ----------------------------------------------------------------------

# # Azure Log Analytics Workspace for ACA
# resource "azurerm_log_analytics_workspace" "log_analytics" {
#   name                = "${var.resource_group_name}-law"
#   location            = azurerm_resource_group.rg.location
#   resource_group_name = azurerm_resource_group.rg.name
#   sku                 = "PerGB2018"

#   retention_in_days   = 30

#   identity {
#     type = "SystemAssigned"
#   }

#   tags = {
#     environment = "production"
#     project     = "big-data-pipeline"
#   }
# }













# # Azure Container Instance for Redis
# resource "azurerm_container_group" "redis" {
#   name                = "whisperer-redis"
#   location            = azurerm_resource_group.rg.location
#   resource_group_name = azurerm_resource_group.rg.name
#   ip_address_type     = "Private"
#   subnet_ids          = [azurerm_subnet.aca_subnet.id]
#   os_type             = "Linux"

#   container {
#     name   = "redis"
#     image  = "redis:7.2-bookworm"
#     cpu    = "0.5"
#     memory = "1"

#     ports {
#       port     = 6379
#       protocol = "TCP"
#     }

#     # Proper Redis configuration
#     commands = [
#       "redis-server",
#       "--appendonly", "yes",
#       "--protected-mode", "no",
#       "--bind", "0.0.0.0",
#       "--port", "6379"
#     ]

#     # Mount for persistence (optional)
#     # volume {
#     #   name                 = "redis-data"
#     #   mount_path          = "/data"
#     #   read_only           = false
#     #   empty_dir           = {}
#     # }
#   }
# }

# # Output the private IP for the worker to use
# output "redis_private_ip" {
#   value = azurerm_container_group.redis.ip_address
# }

# # Updated worker configuration to use Redis private IP
# resource "azurerm_container_app" "whisworker" {
#   count                        = var.images_ready ? 1 : 1
#   name                         = "whisper-worker"
#   container_app_environment_id = azurerm_container_app_environment.aca_env.id
#   resource_group_name          = azurerm_resource_group.rg.name

#   revision_mode = "Single"

#   identity {
#     type         = "UserAssigned"
#     identity_ids = [azurerm_user_assigned_identity.aca_identity.id]
#   }

#   template {
#     container {
#       name   = "worker"
#       image  = "${azurerm_container_registry.acr.login_server}/${var.brick_whisperer_image_name}:latest"
#       cpu    = 1
#       memory = "2.0Gi"

#       env {
#         name  = "CELERY_BROKER_URL"
#         # Use the private IP of the ACI Redis instance
#         value = "redis://${azurerm_container_group.redis.ip_address}:6379"
#       }
#     }

#     min_replicas = 0
#     max_replicas = 5

#     custom_scale_rule {
#       name             = "redis-queue-length"
#       custom_rule_type = "redis"
#       metadata = {
#         "type"            = "redis"
#         # Use the private IP for KEDA as well
#         "address"         = "${azurerm_container_group.redis.ip_address}:6379"
#         "listName"        = "celery"
#         "listLength"      = "5"
#         "activationValue" = "1"
#       }
#     }
#   }

#   registry {
#     server   = azurerm_container_registry.acr.login_server
#     identity = azurerm_user_assigned_identity.aca_identity.id
#   }

#   depends_on = [
#     azurerm_user_assigned_identity.aca_identity,
#     azurerm_role_assignment.aca_identity_acr_pull,
#     azurerm_container_group.redis
#   ]
# }




# # Create Azure Container App for Redis
# resource "azurerm_container_app" "redis" {
#   name                         = "whisperer-redis"
#   container_app_environment_id = azurerm_container_app_environment.aca_env.id
#   resource_group_name          = azurerm_resource_group.rg.name

#   revision_mode = "Single"

#   identity {
#     type         = "UserAssigned"
#     identity_ids = [azurerm_user_assigned_identity.aca_identity.id]
#   }

#   template {
#     container {
#       name   = "redis"
#       image  = "redis:7.2-bookworm"
#       cpu    = 0.5
#       memory = "1.0Gi"

#       env {
#         name  = "ALLOW_EMPTY_PASSWORD"
#         value = "yes"
#       }
#     }

#     min_replicas = 1
#     max_replicas = 1
#   }

#   # registry {
#   #   server   = azurerm_container_registry.acr.login_server
#   #   identity = azurerm_user_assigned_identity.aca_identity.id
#   # }

#   ingress {
#     external_enabled = false
#     target_port      = 6379

#     traffic_weight {
#       latest_revision = true
#       percentage      = 100
#     }
#   }

#   depends_on = [
#     azurerm_user_assigned_identity.aca_identity,
#     azurerm_role_assignment.aca_identity_acr_pull
#   ]
# }




# resource "azurerm_container_group" "redis" {
#   name                = "whisperer-redis"
#   location            = azurerm_resource_group.rg.location
#   resource_group_name = azurerm_resource_group.rg.name
#   ip_address_type     = "Private"
#   subnet_ids          = [azurerm_subnet.aca_subnet.id]
#   os_type             = "Linux"

#   container {
#     name   = "redis"
#     image  = "redis:7.2-bookworm"
#     cpu    = "0.5"
#     memory = "1"

#     ports {
#       port     = 6379
#       protocol = "TCP"
#     }
#   }
# }



# resource "azurerm_container_app" "redis_test" {
#   name                         = "redis-test"
#   container_app_environment_id = azurerm_container_app_environment.aca_env.id
#   resource_group_name          = azurerm_resource_group.rg.name

#   revision_mode = "Single"

#   template {
#     container {
#       name   = "redis-test"
#       image  = "redis:7.2-bookworm"
#       cpu    = 0.25
#       memory = "0.5Gi"

#       command = [
#         "sh", "-c", 
#         "while true; do redis-cli -h whisperer-redis -p 6379 ping && echo 'Redis is reachable' || echo 'Redis connection failed'; sleep 10; done"
#       ]
#     }

#     min_replicas = 1
#     max_replicas = 1
#   }
# }

# resource "azurerm_container_app" "worker" {
#   count                        = var.images_ready ? 1 : 1
#   name                         = "whisperer-worker"
#   container_app_environment_id = azurerm_container_app_environment.aca_env.id
#   resource_group_name          = azurerm_resource_group.rg.name

#   revision_mode = "Single"

#   identity {
#     type         = "UserAssigned"
#     identity_ids = [azurerm_user_assigned_identity.aca_identity.id]
#   }

#   template {
#     container {
#       name   = "worker"
#       image  = "${azurerm_container_registry.acr.login_server}/${var.brick_whisperer_image_name}:latest"
#       cpu    = 1
#       memory = "2.0Gi"

#       env {
#         name  = "CELERY_BROKER_URL"
#         value = "redis://whisperer-redis:6379"
#       }
#     }

#     min_replicas = 0
#     max_replicas = 5

#     custom_scale_rule {
#       name             = "redis-queue-length"
#       custom_rule_type = "redis"
#       metadata = {
#         "type"            = "redis"
#         # Use the full internal FQDN for the scaler
#         "address"         = "whisperer-redis.internal.${azurerm_container_app_environment.aca_env.default_domain}:6379"
#         "listName"        = "celery"
#         "listLength"      = "5"
#         "activationValue" = "1"
#       }
#     }
#   }

#   registry {
#     server   = azurerm_container_registry.acr.login_server
#     identity = azurerm_user_assigned_identity.aca_identity.id
#   }

#   depends_on = [
#     azurerm_user_assigned_identity.aca_identity,
#     azurerm_role_assignment.aca_identity_acr_pull,
#     azurerm_container_app.redis
#   ]
# }
