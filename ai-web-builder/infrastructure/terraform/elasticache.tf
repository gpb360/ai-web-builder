# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "${var.project_name}-redis-subnet-group"
  }
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  family = "redis7.x"
  name   = "${var.project_name}-redis-params"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
  
  parameter {
    name  = "timeout"
    value = "300"
  }
  
  tags = {
    Name = "${var.project_name}-redis-params"
  }
}

# ElastiCache Replication Group
resource "aws_elasticache_replication_group" "main" {
  replication_group_id         = "${var.project_name}-redis"
  description                  = "Redis cluster for AI Web Builder caching"
  
  # Engine Configuration
  engine               = "redis"
  engine_version       = "7.0"
  node_type           = "cache.t3.medium"
  
  # Cluster Configuration
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  # Network Configuration
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  # Parameter Group
  parameter_group_name = aws_elasticache_parameter_group.main.name
  
  # Backup Configuration
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:07:00"
  
  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = random_password.redis_auth_token.result
  
  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format      = "text"
    log_type        = "slow-log"
  }
  
  tags = {
    Name = "${var.project_name}-redis"
  }
  
  lifecycle {
    ignore_changes = [auth_token]
  }
}

# Random auth token for Redis
resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
}

# CloudWatch Log Group for Redis
resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/${var.project_name}-redis/slow-log"
  retention_in_days = 7
  
  tags = {
    Name = "${var.project_name}-redis-slow-log"
  }
}

# Store Redis auth token in Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name        = "${var.project_name}/redis-auth-token"
  description = "Redis auth token for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-redis-auth-token"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id     = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = random_password.redis_auth_token.result
}

# Store full Redis URL in Secrets Manager
resource "aws_secretsmanager_secret" "redis_url" {
  name        = "${var.project_name}/redis-url"
  description = "Complete Redis URL for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-redis-url"
  }
}

resource "aws_secretsmanager_secret_version" "redis_url" {
  secret_id = aws_secretsmanager_secret.redis_url.id
  secret_string = "redis://:${random_password.redis_auth_token.result}@${aws_elasticache_replication_group.main.primary_endpoint_address}:6379"
}

# Outputs
output "redis_primary_endpoint" {
  value = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_reader_endpoint" {
  value = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "redis_port" {
  value = 6379
}