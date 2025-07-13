#!/bin/bash

# AI Web Builder - Setup AWS Secrets Manager
# This script helps configure all required secrets for the production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-web-builder"
AWS_REGION="us-east-1"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_instruction() {
    echo -e "${BLUE}[INSTRUCTION]${NC} $1"
}

# Function to check if AWS CLI is configured
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured"
        print_error "Please run 'aws configure' or set environment variables"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    print_status "Using AWS Account: $account_id"
}

# Function to update a secret
update_secret() {
    local secret_name=$1
    local secret_description=$2
    local current_value=""
    
    # Try to get current value (will fail if secret doesn't exist)
    current_value=$(aws secretsmanager get-secret-value --secret-id "$secret_name" --query SecretString --output text 2>/dev/null || echo "")
    
    if [ -n "$current_value" ] && [ "$current_value" != "REPLACE_WITH_ACTUAL_*" ]; then
        print_status "Secret '$secret_name' already has a value"
        read -p "Do you want to update it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    echo
    print_instruction "Please enter the value for: $secret_description"
    print_instruction "Secret name: $secret_name"
    read -s -p "Enter value: " secret_value
    echo
    
    if [ -z "$secret_value" ]; then
        print_warning "Skipping empty value for $secret_name"
        return 0
    fi
    
    # Update the secret
    aws secretsmanager put-secret-value \
        --secret-id "$secret_name" \
        --secret-string "$secret_value" \
        --region $AWS_REGION >/dev/null
    
    print_status "✅ Updated $secret_name"
}

# Function to setup all secrets
setup_secrets() {
    print_status "Setting up AWS Secrets Manager secrets..."
    echo
    
    # AI API Keys
    print_status "🤖 AI Service API Keys"
    echo "You'll need to obtain these API keys from the respective providers:"
    echo
    
    update_secret "${PROJECT_NAME}/deepseek-api-key" "DeepSeek API Key (from https://platform.deepseek.com/)"
    update_secret "${PROJECT_NAME}/gemini-api-key" "Google Gemini API Key (from https://aistudio.google.com/)"
    
    echo
    print_status "🔗 Platform Integration API Keys"
    echo "These are optional but recommended for full functionality:"
    echo
    
    update_secret "${PROJECT_NAME}/ghl-api-key" "GoHighLevel API Key (from your GHL account)"
    update_secret "${PROJECT_NAME}/simvoly-api-key" "Simvoly API Key (from your Simvoly account)"
    
    echo
    print_status "💳 Payment & Analytics (Optional for MVP)"
    echo "You can set these up later when ready for billing:"
    echo
    
    read -p "Do you want to set up Stripe keys now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Create Stripe secrets if they don't exist
        aws secretsmanager create-secret \
            --name "${PROJECT_NAME}/stripe-secret-key" \
            --description "Stripe secret key for payments" \
            --region $AWS_REGION 2>/dev/null || true
            
        aws secretsmanager create-secret \
            --name "${PROJECT_NAME}/stripe-publishable-key" \
            --description "Stripe publishable key for frontend" \
            --region $AWS_REGION 2>/dev/null || true
            
        update_secret "${PROJECT_NAME}/stripe-secret-key" "Stripe Secret Key (from https://dashboard.stripe.com/)"
        update_secret "${PROJECT_NAME}/stripe-publishable-key" "Stripe Publishable Key (from https://dashboard.stripe.com/)"
    fi
}

# Function to verify secrets
verify_secrets() {
    print_status "Verifying secrets configuration..."
    
    local required_secrets=(
        "${PROJECT_NAME}/database-url"
        "${PROJECT_NAME}/redis-url"
        "${PROJECT_NAME}/jwt-secret"
        "${PROJECT_NAME}/deepseek-api-key"
        "${PROJECT_NAME}/gemini-api-key"
    )
    
    local optional_secrets=(
        "${PROJECT_NAME}/ghl-api-key"
        "${PROJECT_NAME}/simvoly-api-key"
    )
    
    echo
    print_status "📋 Required Secrets Status:"
    
    for secret in "${required_secrets[@]}"; do
        local value=$(aws secretsmanager get-secret-value --secret-id "$secret" --query SecretString --output text 2>/dev/null || echo "")
        if [ -n "$value" ] && [ "$value" != "REPLACE_WITH_ACTUAL_*" ]; then
            print_status "✅ $secret - Configured"
        else
            print_warning "❌ $secret - Missing or placeholder"
        fi
    done
    
    echo
    print_status "📋 Optional Secrets Status:"
    
    for secret in "${optional_secrets[@]}"; do
        local value=$(aws secretsmanager get-secret-value --secret-id "$secret" --query SecretString --output text 2>/dev/null || echo "")
        if [ -n "$value" ] && [ "$value" != "REPLACE_WITH_ACTUAL_*" ]; then
            print_status "✅ $secret - Configured"
        else
            print_status "⚪ $secret - Not configured (optional)"
        fi
    done
}

# Function to show deployment readiness
show_deployment_readiness() {
    echo
    print_status "🚀 Deployment Readiness Check"
    echo
    
    # Check if infrastructure secrets exist (created by Terraform)
    local infra_secrets=(
        "${PROJECT_NAME}/database-url"
        "${PROJECT_NAME}/redis-url"
        "${PROJECT_NAME}/jwt-secret"
    )
    
    local infra_ready=true
    for secret in "${infra_secrets[@]}"; do
        if ! aws secretsmanager describe-secret --secret-id "$secret" --region $AWS_REGION >/dev/null 2>&1; then
            infra_ready=false
            break
        fi
    done
    
    if [ "$infra_ready" = true ]; then
        print_status "✅ Infrastructure secrets exist (Terraform has been deployed)"
    else
        print_warning "❌ Infrastructure secrets missing"
        print_instruction "Run the infrastructure deployment first:"
        print_instruction "  cd infrastructure && ./scripts/deploy.sh --infra-only"
        return 1
    fi
    
    # Check AI API keys
    local ai_keys_ready=true
    local deepseek_value=$(aws secretsmanager get-secret-value --secret-id "${PROJECT_NAME}/deepseek-api-key" --query SecretString --output text 2>/dev/null || echo "")
    local gemini_value=$(aws secretsmanager get-secret-value --secret-id "${PROJECT_NAME}/gemini-api-key" --query SecretString --output text 2>/dev/null || echo "")
    
    if [ -z "$deepseek_value" ] || [ "$deepseek_value" = "REPLACE_WITH_ACTUAL_DEEPSEEK_API_KEY" ]; then
        ai_keys_ready=false
        print_warning "❌ DeepSeek API key not configured"
    else
        print_status "✅ DeepSeek API key configured"
    fi
    
    if [ -z "$gemini_value" ] || [ "$gemini_value" = "REPLACE_WITH_ACTUAL_GEMINI_API_KEY" ]; then
        ai_keys_ready=false
        print_warning "❌ Gemini API key not configured"
    else
        print_status "✅ Gemini API key configured"
    fi
    
    echo
    if [ "$ai_keys_ready" = true ]; then
        print_status "🎉 Ready for deployment!"
        print_instruction "You can now run the full deployment:"
        print_instruction "  cd infrastructure && ./scripts/deploy.sh"
    else
        print_warning "⚠️  AI API keys needed before deployment"
        print_instruction "Please configure the missing API keys and run this script again"
    fi
}

# Function to show API key setup instructions
show_api_key_instructions() {
    echo
    print_status "📚 API Key Setup Instructions"
    echo
    
    print_instruction "🤖 DeepSeek API Key:"
    print_instruction "1. Go to https://platform.deepseek.com/"
    print_instruction "2. Sign up or log in"
    print_instruction "3. Navigate to API Keys section"
    print_instruction "4. Create a new API key"
    print_instruction "5. Copy the key (starts with 'sk-')"
    echo
    
    print_instruction "🧠 Google Gemini API Key:"
    print_instruction "1. Go to https://aistudio.google.com/"
    print_instruction "2. Sign in with Google account"
    print_instruction "3. Click 'Get API Key'"
    print_instruction "4. Create a new API key"
    print_instruction "5. Copy the key"
    echo
    
    print_instruction "🔗 GoHighLevel API Key (Optional):"
    print_instruction "1. Log in to your GoHighLevel account"
    print_instruction "2. Go to Settings > Integrations"
    print_instruction "3. Find API section and generate key"
    echo
    
    print_instruction "🌐 Simvoly API Key (Optional):"
    print_instruction "1. Log in to your Simvoly account"
    print_instruction "2. Go to Account Settings"
    print_instruction "3. Find API Access section"
    print_instruction "4. Generate or copy existing API key"
    echo
}

# Main function
main() {
    print_status "🔐 AI Web Builder - AWS Secrets Manager Setup"
    print_status "This script will help you configure all required secrets for production deployment"
    echo
    
    # Parse command line arguments
    local show_instructions=false
    local verify_only=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --instructions)
                show_instructions=true
                shift
                ;;
            --verify)
                verify_only=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --instructions    Show API key setup instructions"
                echo "  --verify         Only verify current secrets status"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_aws_credentials
    
    if [ "$show_instructions" = true ]; then
        show_api_key_instructions
        exit 0
    fi
    
    if [ "$verify_only" = true ]; then
        verify_secrets
        show_deployment_readiness
        exit 0
    fi
    
    # Main setup flow
    setup_secrets
    verify_secrets
    show_deployment_readiness
    
    echo
    print_status "🎯 Next Steps:"
    print_instruction "1. If any API keys are missing, get them from the providers"
    print_instruction "2. Run this script again to update missing keys"
    print_instruction "3. When all keys are configured, deploy the application"
    print_instruction "4. Monitor the CloudWatch dashboard for performance"
    echo
    print_status "For API key setup instructions, run: $0 --instructions"
}

# Run main function with all arguments
main "$@"