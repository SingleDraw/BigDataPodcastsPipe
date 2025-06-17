
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

# 2. Create Azure Subnet for ACA 🕸️
data "azurerm_subnet" "aca_subnet" {
  name                 = "aca-subnet"
  virtual_network_name = "aca-vnet"  # Ensure this matches your VNet name
  resource_group_name  = data.azurerm_resource_group.rg.name
}

# 3. Create ACA environment for Big Data Processing 🌍
data "azurerm_container_app_environment" "aca_env" {
  name                = "whisperer-aca-env"
  resource_group_name = data.azurerm_resource_group.rg.name
}

# 4. Create user-assigned managed identity for ACA 🧑‍💼
data "azurerm_user_assigned_identity" "aca_identity" {
  name                = "whisperer-aca-identity"
  resource_group_name = data.azurerm_resource_group.rg.name
}

#----------------------------------------------------------------------------------
# Manage new Azure resources for the BigDataPipe project
#----------------------------------------------------------------------------------


# Create Azure Container App for Redis
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
      
      # Add Redis configuration for better connectivity
      args = ["redis-server", "--bind", "0.0.0.0", "--protected-mode", "no"]
    }



    min_replicas = 1
    max_replicas = 1
  }

  # if image are stored in ACR and used here, uncomment the registry block
  # registry {
  #   server   = azurerm_container_registry.acr.login_server
  #   identity = azurerm_user_assigned_identity.aca_identity.id
  # }

  ingress {
    external_enabled = false  # Internal access only
    target_port      = 6379
    transport        = "tcp" # Use TCP for Redis

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}


resource "azurerm_container_app" "redis_test" {
  name                         = "redis-test"
  container_app_environment_id = data.azurerm_container_app_environment.aca_env.id
  resource_group_name          = data.azurerm_resource_group.rg.name

  revision_mode = "Single"

  template {
    container {
      name   = "redis-test"
      image  = "redis:7.2-bookworm"
      cpu    = 0.25
      memory = "0.5Gi"

      # Updated command with better error handling and debugging
      command = [
        "sh", "-c", 
        <<-EOT
        # Install netcat for testing connectivity
        apt-get update && apt-get install -y dnsutils netcat-openbsd redis-tools
        echo "Starting Redis connectivity test..."
        while true; do 
          echo "Attempting to connect to whisperer-redis:6379..."
          
          # Test basic connectivity first
          if nc -z whisperer-redis 6379 2>/dev/null; then
            echo "Port 6379 is reachable on whisperer-redis"
            
            # Test Redis ping
            if redis-cli -h whisperer-redis -p 6379 ping; then
              echo "Redis PING successful at $(date)"
            else
              echo "Redis PING failed at $(date)"
            fi
          else
            echo "Cannot reach whisperer-redis:6379 at $(date)"
            
            # Try to resolve the hostname
            nslookup whisperer-redis || echo "DNS resolution failed"
          fi
          
          echo "Waiting 30 seconds before next test..."
          sleep 30
        done
        EOT
      ]
    }

    min_replicas = 1
    max_replicas = 1
  }
}

