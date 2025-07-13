# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# RDS Parameter Group
resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${var.project_name}-postgres-params"
  
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }
  
  parameter {
    name  = "log_statement"
    value = "all"
  }
  
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
  
  tags = {
    Name = "${var.project_name}-postgres-params"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-postgres"
  
  # Engine Configuration
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"
  
  # Storage Configuration
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type         = "gp3"
  storage_encrypted    = true
  
  # Database Configuration
  db_name  = "ai_web_builder"
  username = "postgres"
  password = random_password.db_password.result
  
  # Network Configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = false
  
  # Backup Configuration
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Monitoring Configuration
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
  
  # Parameter Group
  parameter_group_name = aws_db_parameter_group.main.name
  
  # Deletion Protection
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.project_name}-postgres-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  tags = {
    Name = "${var.project_name}-postgres"
  }
  
  lifecycle {
    ignore_changes = [password]
  }
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# IAM Role for RDS Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Store database password in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.project_name}/database-password"
  description = "Database password for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# Store full database URL in Secrets Manager
resource "aws_secretsmanager_secret" "database_url" {
  name        = "${var.project_name}/database-url"
  description = "Complete database URL for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-database-url"
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql://${aws_db_instance.main.username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
}

# Outputs
output "database_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "database_port" {
  value = aws_db_instance.main.port
}

output "database_name" {
  value = aws_db_instance.main.db_name
}