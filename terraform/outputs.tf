output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "location" {
  description = "Azure region where resources are deployed"
  value       = azurerm_resource_group.main.location
}

# Container Registry
output "acr_login_server" {
  description = "Login server URL for Azure Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  description = "Admin username for Azure Container Registry"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "Admin password for Azure Container Registry"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}

# Storage Account
output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.data.name
}

output "storage_primary_connection_string" {
  description = "Primary connection string for storage account"
  value       = azurerm_storage_account.data.primary_connection_string
  sensitive   = true
}

output "storage_primary_access_key" {
  description = "Primary access key for storage account"
  value       = azurerm_storage_account.data.primary_access_key
  sensitive   = true
}

# Container App
output "api_url" {
  description = "URL of the deployed API"
  value       = "https://${azurerm_container_app.api.latest_revision_fqdn}"
}

output "api_fqdn" {
  description = "Fully qualified domain name of the API"
  value       = azurerm_container_app.api.latest_revision_fqdn
}

# Application Insights
output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

# Deployment Instructions
output "deployment_instructions" {
  description = "Next steps for deployment"
  value = <<-EOT
  
  ===== Deployment Instructions =====
  
  1. Login to Azure Container Registry:
     az acr login --name ${azurerm_container_registry.acr.name}
  
  2. Build and push Docker image:
     docker build -t ${azurerm_container_registry.acr.login_server}/${var.api_image_name}:${var.api_image_tag} .
     docker push ${azurerm_container_registry.acr.login_server}/${var.api_image_name}:${var.api_image_tag}
  
  3. Access your API at:
     https://${azurerm_container_app.api.latest_revision_fqdn}
  
  4. API Documentation:
     https://${azurerm_container_app.api.latest_revision_fqdn}/docs
  
  5. Upload data to storage:
     az storage blob upload-batch \
       --account-name ${azurerm_storage_account.data.name} \
       --destination predictions \
       --source data/predictions/
  
  6. Monitor logs:
     az containerapp logs show \
       --name ${azurerm_container_app.api.name} \
       --resource-group ${azurerm_resource_group.main.name} \
       --follow
  
  ===================================
  EOT
}
