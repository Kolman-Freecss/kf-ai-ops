# Configuration variables for AI-Ops Infrastructure

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging or production."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "container_image" {
  description = "API container image"
  type        = string
  default     = "ai-ops-api:latest"
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "log_retention_days" {
  description = "Log retention days"
  type        = number
  default     = 30
}

variable "enable_monitoring" {
  description = "Enable advanced monitoring"
  type        = bool
  default     = true
}

variable "ai_optimizer_config" {
  description = "AI optimizer configuration"
  type = object({
    enabled            = bool
    auto_apply         = bool
    confidence_threshold = number
  })
  default = {
    enabled              = true
    auto_apply           = false
    confidence_threshold = 0.8
  }
}
