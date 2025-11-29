variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "pandemic-tracker"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "Southeast Asia"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Pandemic Outbreak Tracker"
    ManagedBy   = "Terraform"
    Environment = "dev"
  }
}

# Container Registry
variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Basic"
  
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

# Storage
variable "storage_replication_type" {
  description = "Storage account replication type"
  type        = string
  default     = "LRS"
  
  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS"], var.storage_replication_type)
    error_message = "Must be LRS, GRS, RAGRS, or ZRS."
  }
}

# Logging
variable "log_retention_days" {
  description = "Log retention in days"
  type        = number
  default     = 30
}

# Container App - API
variable "api_image_name" {
  description = "Docker image name for the API"
  type        = string
  default     = "pandemic-tracker-api"
}

variable "api_image_tag" {
  description = "Docker image tag for the API"
  type        = string
  default     = "latest"
}

variable "api_cpu" {
  description = "CPU cores for API container (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)"
  type        = number
  default     = 0.5
}

variable "api_memory" {
  description = "Memory for API container in Gi (0.5Gi, 1.0Gi, 1.5Gi, 2.0Gi, 3.0Gi, 3.5Gi, 4.0Gi)"
  type        = string
  default     = "1Gi"
}

variable "api_min_replicas" {
  description = "Minimum number of API replicas"
  type        = number
  default     = 1
}

variable "api_max_replicas" {
  description = "Maximum number of API replicas"
  type        = number
  default     = 3
}

# CORS Configuration
variable "cors_origins" {
  description = "Allowed CORS origins for the API"
  type        = list(string)
  default     = ["*"]
}
