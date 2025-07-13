# Generate JWT Secret
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# JWT Secret in Secrets Manager
resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "${var.project_name}/jwt-secret"
  description = "JWT secret key for AI Web Builder authentication"
  
  tags = {
    Name = "${var.project_name}-jwt-secret"
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

# DeepSeek API Key (placeholder - need to set manually)
resource "aws_secretsmanager_secret" "deepseek_api_key" {
  name        = "${var.project_name}/deepseek-api-key"
  description = "DeepSeek API key for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-deepseek-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "deepseek_api_key" {
  secret_id     = aws_secretsmanager_secret.deepseek_api_key.id
  secret_string = "REPLACE_WITH_ACTUAL_DEEPSEEK_API_KEY"
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Gemini API Key (placeholder - need to set manually)
resource "aws_secretsmanager_secret" "gemini_api_key" {
  name        = "${var.project_name}/gemini-api-key"
  description = "Google Gemini API key for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-gemini-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "gemini_api_key" {
  secret_id     = aws_secretsmanager_secret.gemini_api_key.id
  secret_string = "REPLACE_WITH_ACTUAL_GEMINI_API_KEY"
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# GoHighLevel API Key (placeholder - need to set manually)
resource "aws_secretsmanager_secret" "ghl_api_key" {
  name        = "${var.project_name}/ghl-api-key"
  description = "GoHighLevel API key for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-ghl-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "ghl_api_key" {
  secret_id     = aws_secretsmanager_secret.ghl_api_key.id
  secret_string = "REPLACE_WITH_ACTUAL_GHL_API_KEY"
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Simvoly API Key (placeholder - need to set manually)
resource "aws_secretsmanager_secret" "simvoly_api_key" {
  name        = "${var.project_name}/simvoly-api-key"
  description = "Simvoly API key for AI Web Builder"
  
  tags = {
    Name = "${var.project_name}-simvoly-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "simvoly_api_key" {
  secret_id     = aws_secretsmanager_secret.simvoly_api_key.id
  secret_string = "REPLACE_WITH_ACTUAL_SIMVOLY_API_KEY"
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Outputs
output "secret_arns" {
  value = {
    database_url       = aws_secretsmanager_secret.database_url.arn
    redis_url         = aws_secretsmanager_secret.redis_url.arn
    jwt_secret        = aws_secretsmanager_secret.jwt_secret.arn
    deepseek_api_key  = aws_secretsmanager_secret.deepseek_api_key.arn
    gemini_api_key    = aws_secretsmanager_secret.gemini_api_key.arn
    ghl_api_key       = aws_secretsmanager_secret.ghl_api_key.arn
    simvoly_api_key   = aws_secretsmanager_secret.simvoly_api_key.arn
  }
}