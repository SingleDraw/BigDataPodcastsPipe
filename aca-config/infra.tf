# terraform/main.tf
resource "azurerm_container_app_environment" "main" {
  name                = "aca-env-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app_job" "job_submitter" {
  name                         = "job-submitter"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  
  template {
    container {
      name   = "job-submitter"
      image  = "${var.container_registry}/job-submitter:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }
  
  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }
}

resource "azurerm_container_app" "redis" {
  name                         = "redis-broker"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group_name
  
  template {
    min_replicas = 0
    max_replicas = 1
    
    container {
      name   = "redis"
      image  = "redis:alpine"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }
  
  ingress {
    external_enabled = false
    target_port      = 6379
  }
}