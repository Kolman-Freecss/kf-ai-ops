# AI-Ops Infrastructure Outputs

output "environment" {
  description = "Deployed environment"
  value       = var.environment
}

output "region" {
  description = "AWS region"
  value       = var.region
}

output "networking" {
  description = "Networking information"
  value = {
    vpc_id             = module.networking.vpc_id
    public_subnet_ids  = module.networking.public_subnet_ids
    private_subnet_ids = module.networking.private_subnet_ids
  }
}

output "compute" {
  description = "Compute information"
  value = {
    api_endpoint = module.compute.api_endpoint
    cluster_name = module.compute.cluster_name
  }
}

output "observability" {
  description = "Observability information"
  value = {
    otel_endpoint    = module.observability.otel_endpoint
    dashboard_url    = module.observability.dashboard_url
    traces_log_group = module.observability.traces_log_group
  }
}

output "quick_start" {
  description = "Quick start commands"
  value = <<-EOT
    
    🚀 AI-Ops Infrastructure Deployed!
    
    API Endpoint: ${module.compute.api_endpoint}
    Dashboard:    ${module.observability.dashboard_url}
    
    Next steps:
    1. Configure OTEL_EXPORTER_OTLP_ENDPOINT=${module.observability.otel_endpoint}
    2. Verify health: curl ${module.compute.api_endpoint}/health
    3. View traces in CloudWatch dashboard
    
  EOT
}
