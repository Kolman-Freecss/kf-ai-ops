# Observability Module
# Complete stack: metrics, traces, and logs

variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "retention_days" {
  type    = number
  default = 30
}

# CloudWatch Log Groups for observability
resource "aws_cloudwatch_log_group" "traces" {
  name              = "/ai-ops/${var.environment}/traces"
  retention_in_days = var.retention_days

  tags = {
    Name = "${var.name_prefix}-traces"
    Type = "observability"
  }
}

resource "aws_cloudwatch_log_group" "metrics" {
  name              = "/ai-ops/${var.environment}/metrics"
  retention_in_days = var.retention_days

  tags = {
    Name = "${var.name_prefix}-metrics"
    Type = "observability"
  }
}

# X-Ray for distributed tracing
resource "aws_xray_sampling_rule" "main" {
  rule_name      = "${var.name_prefix}-sampling"
  priority       = 1000
  version        = 1
  reservoir_size = 5
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  attributes = {}
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "API Requests"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "${var.name_prefix}-api"],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", "${var.name_prefix}-api"]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Request Latency"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/X-Ray", "ResponseTime", "ServiceName", "${var.name_prefix}-api"]
          ]
          period = 60
          stat   = "p99"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 6
        properties = {
          title  = "Recent Logs"
          region = data.aws_region.current.name
          query  = "SOURCE '/ecs/${var.name_prefix}' | fields @timestamp, @message | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 8
        height = 6
        properties = {
          title  = "AI Optimizations Applied"
          region = data.aws_region.current.name
          metrics = [
            ["AI-Ops", "OptimizationsApplied", "Environment", var.environment]
          ]
          period = 3600
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 12
        width  = 8
        height = 6
        properties = {
          title  = "Pipeline Duration Trend"
          region = data.aws_region.current.name
          metrics = [
            ["AI-Ops", "PipelineDuration", "Environment", var.environment]
          ]
          period = 3600
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 12
        width  = 8
        height = 6
        properties = {
          title  = "Error Rate"
          region = data.aws_region.current.name
          metrics = [
            ["AI-Ops", "ErrorRate", "Environment", var.environment]
          ]
          period = 300
          stat   = "Average"
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.name_prefix}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorRate"
  namespace           = "AI-Ops"
  period              = 300
  statistic           = "Average"
  threshold           = 5
  alarm_description   = "Error rate is above 5%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Environment = var.environment
  }

  tags = {
    Name = "${var.name_prefix}-error-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "slow_pipeline" {
  alarm_name          = "${var.name_prefix}-slow-pipeline"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "PipelineDuration"
  namespace           = "AI-Ops"
  period              = 3600
  statistic           = "Average"
  threshold           = 600000  # 10 minutes in ms
  alarm_description   = "Pipeline duration exceeds 10 minutes"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Environment = var.environment
  }

  tags = {
    Name = "${var.name_prefix}-pipeline-alarm"
  }
}

# Data sources
data "aws_region" "current" {}

# Outputs
output "otel_endpoint" {
  description = "OpenTelemetry collector endpoint"
  value       = "http://localhost:4317"  # In production this would be a real endpoint
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${var.name_prefix}-dashboard"
}

output "traces_log_group" {
  value = aws_cloudwatch_log_group.traces.name
}

output "metrics_log_group" {
  value = aws_cloudwatch_log_group.metrics.name
}
