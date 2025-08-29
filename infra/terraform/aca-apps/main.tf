
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

# 7. ACR credentials in Key Vault
data "azurerm_key_vault_secret" "acr_username" {
  name         = "acr-admin-username"
  key_vault_id = data.azurerm_key_vault.kv.id
}

data "azurerm_key_vault_secret" "acr_password" {
  name         = "acr-admin-password"
  key_vault_id = data.azurerm_key_vault.kv.id
}

data "azurerm_key_vault_secret" "blob_connection_string" {
  name         = var.blob_connection_string_name
  key_vault_id = data.azurerm_key_vault.kv.id
}

# 8. Azure Subnet for ACA 🕸️
data "azurerm_subnet" "aca_subnet" {
  name                 = "aca-subnet"
  virtual_network_name = "aca-vnet"  # Ensure this matches your VNet name
  resource_group_name  = data.azurerm_resource_group.rg.name
}

# 9. ACA environment for Big Data Processing 🌍
data "azurerm_container_app_environment" "aca_env" {
  name                = "whisperer-aca-env"
  resource_group_name = data.azurerm_resource_group.rg.name
}

# 10. User-assigned managed identity for ACA 🧑‍💼
data "azurerm_user_assigned_identity" "aca_identity" {
  name                = "whisperer-aca-identity"
  resource_group_name = data.azurerm_resource_group.rg.name
}

#----------------------------------------------------------------------------------
# Manage new Azure resources for the BigDataPipe project
#----------------------------------------------------------------------------------

# 1. Create Azure Container App for Redis
resource "azurerm_container_app" "redis" {
  name                         = "whisperer-redis"
  container_app_environment_id = data.azurerm_container_app_environment.aca_env.id
  resource_group_name          = data.azurerm_resource_group.rg.name

  revision_mode = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [data.azurerm_user_assigned_identity.aca_identity.id]
  }

  template {
    container {
      name   = "redis"
      image  = "redis:7.2-bookworm"
      cpu    = 0.5
      memory = "1.0Gi"

      env {
        name  = "ALLOW_EMPTY_PASSWORD"
        value = "yes"
      }      
      
      # Redis configuration for Container Apps
      args = [
        "redis-server", 
        "--bind", "0.0.0.0", 
        "--protected-mode", "no", 
        "--tcp-keepalive", "60",
        "--port", "6379"
      ]

    }

    min_replicas = 1
    max_replicas = 1

  }

  # Ingresss configuration for Redis
  # Note: We dont use it externally, so we disable external access
  #       and use internal FQDN for communication between services
  ingress {
    external_enabled = false  # Internal access only
    target_port      = 6379
    transport        = "tcp"  # TCP is required for Redis

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}

# variable "redis_address" {
#   description = "Internal address of the Redis container app"
#   type        = string
#   default     = "${azurerm_container_app.redis.name}.${data.azurerm_container_app_environment.aca_env.default_domain}:6379"
# }

# 2. Create Azure Container App for Whisperer Worker
resource "azurerm_container_app" "whisperer_worker" {
  name                         = "whisperer-worker"
  container_app_environment_id = data.azurerm_container_app_environment.aca_env.id
  resource_group_name          = data.azurerm_resource_group.rg.name

  revision_mode = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [data.azurerm_user_assigned_identity.aca_identity.id]
  }

  template {
    container {
      name   = "whisperer-worker"
      image  = "${data.azurerm_container_registry.acr.login_server}/${var.brick_whisperer_image_name}:latest"
      cpu    = 1
      memory = "2.0Gi"

      command = ["whisperer-worker"]

      env {
        name  = "CELERY_BROKER_URL"
        value = "redis://whisperer-redis:6379/0"  # Use the internal FQDN for Redis
      }




      # Add explicit Celery configuration for better KEDA integration
      env {
        name  = "CELERY_TASK_ROUTES"
        value = "{\"*\": {\"queue\": \"transcription_queue\"}}"  # Ensure all tasks go to 'celery' queue
      }

      env {
        name  = "CELERY_TASK_SERIALIZER"
        value = "json"
      }

      env {
        name  = "CELERY_RESULT_SERIALIZER"  
        value = "json"
      }


      env {
        name  = "REDIS_HOST"
        value = "whisperer-redis"
      }

      env {
        name  = "REDIS_PORT"
        value = "6379"
      }

      env {
        name  = "REDIS_DB"
        value = "0"
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = var.storage_account_name
      }
      env {
        # For Connection String approach - refactor Whisperer to use Key Vault or IAM + DefaultCredential
        name  = "AZURE_STORAGE_ACCOUNT_KEY"
        value = "placeholder-for-connection-string"  # Replace with actual connection string or use Key Vault
      }

      # Other environment variables
      env {
        name  = "TASK_TIME_LIMIT"
        value = "1000"
      }
      env {
        name  = "TRANSCRIPTION_LANGUAGE"
        value = "en"
      }
      env {
        name  = "TZ"
        value = "Europe/Warsaw"
      }

    }

    min_replicas = 0
    max_replicas = 5

    # Alternative: Scale based on CPU if Redis queue monitoring is problematic
    # custom_scale_rule {
    #   name             = "cpu-scaling"
    #   custom_rule_type = "cpu"
    #   metadata = {
    #     "type" = "Utilization"
    #     "value" = "70"
    #   }
    # }

    custom_scale_rule {
      name             = "redis-queue-length"
      custom_rule_type = "redis"
      metadata = {
        # "type"            = "redis"
        # Use the full internal FQDN for the scaler
        "address"         = "whisperer-redis:6379"  # Use consistent addressing
        # "address"         = "whisperer-redis.internal.${data.azurerm_container_app_environment.aca_env.default_domain}:6379"
        "databaseIndex"   = "0"               # Specify database index  
        "listName"        = "transcription_queue" # Celery queue name
        "listLength"      = "1"                   # Scale when queue has 5+ items 
        "activationValue" = "1"                   # Activate scaling at 1+ items     
        # Add these additional parameters for better KEDA Redis connectivity
        "enableTLS"       = "false"
        "unsafeSsl"       = "false"
      }
      # fallback { #### DOESNT WORK YET
      #   failure_count = 3  # Retry up to 3 times before fallback
      #   replicas      = 0  # Fallback to 1 replica if Redis is not available
      #   ## Uncomment to use fixed scaling as a fallback
      #   # type = "fixed"
      #   # metadata = {
      #   #   "replicas" = "1"  # Fallback to 0 replica if Redis is not available
      #   # }
      #   ## Uncomment to use CPU scaling as a fallback
      #   # type = "cpu"
      #   # metadata = {
      #   #   "type"  = "Utilization"
      #   #   "value" = "70"  # Scale based on CPU utilization if Redis queue is not available
      #   # }
      # }
    }
  }




  # use ACR for the worker image
  registry {
    server   = data.azurerm_container_registry.acr.login_server
    identity = data.azurerm_user_assigned_identity.aca_identity.id
  }

  depends_on = [
    azurerm_container_app.redis
  ]

  # Add a short delay to ensure Redis is fully ready
  lifecycle {
    replace_triggered_by = [
      azurerm_container_app.redis
    ],
    ignore_changes = [
      template[0].min_replicas,  # Ignore min_replicas changes to allow KEDA to manage scaling
    ]
  }
}

# # Apply KEDA ScaledObject with fallback using kubectl
# resource "null_resource" "apply_keda_scaledobject" {
#   provisioner "local-exec" {
#     command = "kubectl apply -f ${path.module}/keda_scaledobject.yaml"
#   }

#   depends_on = [azurerm_container_app.whisperer_worker]
# }


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


# # Azure Container Instance for Redis - ACI Container Group
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
