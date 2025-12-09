# AI-Ops Infrastructure
# Manages observability and compute infrastructure

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Backend for remote state (uncomment for production)
  # backend "s3" {
  #   bucket         = "ai-ops-terraform-state"
  #   key            = "state/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "ai-ops-terraform-locks"
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "ai-ops"
      Environment = var.environment
      ManagedBy   = "opentofu"
    }
  }
}

# Local values for configuration
locals {
  name_prefix = "ai-ops-${var.environment}"
  
  common_tags = {
    Project     = "ai-ops"
    Environment = var.environment
  }
}

# Random suffix for unique resources
resource "random_id" "suffix" {
  byte_length = 4
}

# VPC for infrastructure
module "networking" {
  source = "./modules/networking"

  name_prefix  = local.name_prefix
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  
  availability_zones = var.availability_zones
}

# Compute cluster (simplified ECS/EKS)
module "compute" {
  source = "./modules/compute"

  name_prefix    = local.name_prefix
  environment    = var.environment
  vpc_id         = module.networking.vpc_id
  subnet_ids     = module.networking.private_subnet_ids
  
  container_image = var.container_image
  container_port  = var.container_port
  
  # OpenTelemetry config
  otel_endpoint = module.observability.otel_endpoint
}

# Observability stack
module "observability" {
  source = "./modules/observability"

  name_prefix = local.name_prefix
  environment = var.environment
  vpc_id      = module.networking.vpc_id
  subnet_ids  = module.networking.private_subnet_ids
  
  retention_days = var.log_retention_days
}

# Main outputs
output "api_endpoint" {
  description = "API endpoint"
  value       = module.compute.api_endpoint
}

output "otel_endpoint" {
  description = "OpenTelemetry collector endpoint"
  value       = module.observability.otel_endpoint
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}
