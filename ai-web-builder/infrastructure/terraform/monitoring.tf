# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", aws_ecs_service.backend.name, "ClusterName", aws_ecs_cluster.main.name],
            ["AWS/ECS", "MemoryUtilization", "ServiceName", aws_ecs_service.backend.name, "ClusterName", aws_ecs_cluster.main.name]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Service Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main.arn_suffix],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main.arn_suffix]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Load Balancer Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.main.id],
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", aws_db_instance.main.id]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", "${aws_elasticache_replication_group.main.replication_group_id}-001"],
            ["AWS/ElastiCache", "CacheHitRate", "CacheClusterId", "${aws_elasticache_replication_group.main.replication_group_id}-001"]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Redis Metrics"
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.project_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ServiceName = aws_ecs_service.backend.name
    ClusterName = aws_ecs_cluster.main.name
  }
  
  tags = {
    Name = "${var.project_name}-high-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "${var.project_name}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ServiceName = aws_ecs_service.backend.name
    ClusterName = aws_ecs_cluster.main.name
  }
  
  tags = {
    Name = "${var.project_name}-high-memory-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "target_response_time" {
  alarm_name          = "${var.project_name}-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "120"
  statistic           = "Average"
  threshold           = "2"
  alarm_description   = "This metric monitors ALB target response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
  
  tags = {
    Name = "${var.project_name}-high-response-time-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.project_name}-database-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
  
  tags = {
    Name = "${var.project_name}-database-high-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.project_name}-redis-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors Redis CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    CacheClusterId = "${aws_elasticache_replication_group.main.replication_group_id}-001"
  }
  
  tags = {
    Name = "${var.project_name}-redis-high-cpu-alarm"
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"
  
  tags = {
    Name = "${var.project_name}-alerts"
  }
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "alerts@ai-web-builder.com"  # Replace with actual email
}

# Custom Metrics for AI Cost Tracking
resource "aws_cloudwatch_log_metric_filter" "ai_cost_tracking" {
  name           = "${var.project_name}-ai-cost-tracking"
  log_group_name = aws_cloudwatch_log_group.backend.name
  pattern        = "[timestamp, request_id, level=\"INFO\", message=\"AI_COST\", cost]"
  
  metric_transformation {
    name      = "AICostPerRequest"
    namespace = "AI-Web-Builder/Costs"
    value     = "$cost"
    unit      = "None"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_ai_costs" {
  alarm_name          = "${var.project_name}-high-ai-costs"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "AICostPerRequest"
  namespace           = "AI-Web-Builder/Costs"
  period              = "300"
  statistic           = "Average"
  threshold           = "0.5"  # Alert if average cost per request exceeds $0.50
  alarm_description   = "This metric monitors AI costs per request"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"
  
  tags = {
    Name = "${var.project_name}-high-ai-costs-alarm"
  }
}

# Custom Metrics for Cache Hit Rate
resource "aws_cloudwatch_log_metric_filter" "cache_hit_rate" {
  name           = "${var.project_name}-cache-hit-rate"
  log_group_name = aws_cloudwatch_log_group.backend.name
  pattern        = "[timestamp, request_id, level=\"INFO\", message=\"CACHE_HIT\"]"
  
  metric_transformation {
    name      = "CacheHits"
    namespace = "AI-Web-Builder/Cache"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "cache_miss_rate" {
  name           = "${var.project_name}-cache-miss-rate"
  log_group_name = aws_cloudwatch_log_group.backend.name
  pattern        = "[timestamp, request_id, level=\"INFO\", message=\"CACHE_MISS\"]"
  
  metric_transformation {
    name      = "CacheMisses"
    namespace = "AI-Web-Builder/Cache"
    value     = "1"
    unit      = "Count"
  }
}

# Outputs
output "dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}