#!/bin/bash

# AI Web Builder Production Deployment Script
# This script deploys the AI Web Builder platform to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-web-builder"
AWS_REGION="us-east-1"
ENVIRONMENT="production"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
check_requirements() {
    print_status "Checking required tools..."
    
    local missing_tools=()
    
    if ! command_exists aws; then
        missing_tools+=("aws-cli")
    fi
    
    if ! command_exists terraform; then
        missing_tools+=("terraform")
    fi
    
    if ! command_exists docker; then
        missing_tools+=("docker")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_error "Please install them and try again"
        exit 1
    fi
    
    print_status "All required tools are available"
}

# Check AWS credentials
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

# Initialize Terraform
init_terraform() {
    print_status "Initializing Terraform..."
    
    cd infrastructure/terraform
    
    # Create S3 bucket for state if it doesn't exist
    local state_bucket="${PROJECT_NAME}-terraform-state"
    if ! aws s3 ls "s3://$state_bucket" >/dev/null 2>&1; then
        print_status "Creating Terraform state bucket..."
        aws s3 mb "s3://$state_bucket" --region $AWS_REGION
        aws s3api put-bucket-versioning --bucket $state_bucket --versioning-configuration Status=Enabled
        aws s3api put-bucket-encryption --bucket $state_bucket --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    fi
    
    terraform init
    cd ../..
}

# Plan infrastructure
plan_infrastructure() {
    print_status "Planning infrastructure changes..."
    
    cd infrastructure/terraform
    terraform plan -var="environment=$ENVIRONMENT" -var="aws_region=$AWS_REGION"
    cd ../..
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure..."
    
    cd infrastructure/terraform
    terraform apply -auto-approve -var="environment=$ENVIRONMENT" -var="aws_region=$AWS_REGION"
    cd ../..
    
    print_status "Infrastructure deployment completed"
}

# Build and push Docker image
build_and_push_image() {
    print_status "Building and pushing Docker image..."
    
    # Get ECR repository URL
    local ecr_repo=$(aws ecr describe-repositories --repository-names ${PROJECT_NAME}-backend --query 'repositories[0].repositoryUri' --output text 2>/dev/null || echo "")
    
    if [ -z "$ecr_repo" ]; then
        print_error "ECR repository not found. Please deploy infrastructure first."
        exit 1
    fi
    
    print_status "ECR Repository: $ecr_repo"
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ecr_repo
    
    # Build image
    print_status "Building Docker image..."
    docker build -t ${PROJECT_NAME}-backend ./backend
    
    # Tag image
    docker tag ${PROJECT_NAME}-backend:latest $ecr_repo:latest
    docker tag ${PROJECT_NAME}-backend:latest $ecr_repo:$(date +%Y%m%d-%H%M%S)
    
    # Push image
    print_status "Pushing Docker image..."
    docker push $ecr_repo:latest
    docker push $ecr_repo:$(date +%Y%m%d-%H%M%S)
    
    print_status "Docker image pushed successfully"
}

# Update ECS service
update_ecs_service() {
    print_status "Updating ECS service..."
    
    local cluster_name="${PROJECT_NAME}-cluster"
    local service_name="${PROJECT_NAME}-backend"
    
    # Force new deployment
    aws ecs update-service \
        --cluster $cluster_name \
        --service $service_name \
        --force-new-deployment \
        --region $AWS_REGION
    
    print_status "Waiting for service to stabilize..."
    aws ecs wait services-stable \
        --cluster $cluster_name \
        --services $service_name \
        --region $AWS_REGION
    
    print_status "ECS service updated successfully"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    local cluster_name="${PROJECT_NAME}-cluster"
    local task_definition="${PROJECT_NAME}-backend"
    
    # Get subnet and security group IDs
    local private_subnets=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-subnet-*" --query 'Subnets[].SubnetId' --output text | tr '\t' ',')
    local security_group=$(aws ec2 describe-security-groups --filters "Name=tag:Name,Values=${PROJECT_NAME}-backend-sg" --query 'SecurityGroups[0].GroupId' --output text)
    
    # Run migration task
    local task_arn=$(aws ecs run-task \
        --cluster $cluster_name \
        --task-definition $task_definition \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$private_subnets],securityGroups=[$security_group],assignPublicIp=DISABLED}" \
        --overrides '{
            "containerOverrides": [
                {
                    "name": "'${PROJECT_NAME}'-backend",
                    "command": ["python", "-m", "alembic", "upgrade", "head"]
                }
            ]
        }' \
        --query 'tasks[0].taskArn' \
        --output text)
    
    print_status "Migration task started: $task_arn"
    
    # Wait for task to complete
    aws ecs wait tasks-stopped --cluster $cluster_name --tasks $task_arn --region $AWS_REGION
    
    # Check task exit code
    local exit_code=$(aws ecs describe-tasks --cluster $cluster_name --tasks $task_arn --query 'tasks[0].containers[0].exitCode' --output text)
    
    if [ "$exit_code" = "0" ]; then
        print_status "Database migrations completed successfully"
    else
        print_error "Database migrations failed with exit code: $exit_code"
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Get load balancer URL
    local lb_dns=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-alb --query 'LoadBalancers[0].DNSName' --output text)
    local api_url="https://$lb_dns/health"
    
    print_status "Testing API endpoint: $api_url"
    
    # Wait for load balancer to be ready
    sleep 30
    
    # Test health endpoint
    local response=$(curl -s -o /dev/null -w "%{http_code}" $api_url || echo "000")
    
    if [ "$response" = "200" ]; then
        print_status "✅ Deployment verification successful!"
        print_status "API is responding at: $api_url"
    else
        print_warning "⚠️  API health check returned: $response"
        print_warning "This might be normal if the service is still starting up"
    fi
}

# Main deployment function
main() {
    print_status "🚀 Starting AI Web Builder deployment..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Region: $AWS_REGION"
    echo
    
    # Parse command line arguments
    local deploy_infra=true
    local deploy_app=true
    local run_migrations_flag=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --infra-only)
                deploy_app=false
                run_migrations_flag=false
                shift
                ;;
            --app-only)
                deploy_infra=false
                shift
                ;;
            --skip-migrations)
                run_migrations_flag=false
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --infra-only      Deploy infrastructure only"
                echo "  --app-only        Deploy application only (skip infrastructure)"
                echo "  --skip-migrations Skip database migrations"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run checks
    check_requirements
    check_aws_credentials
    
    # Deploy infrastructure
    if [ "$deploy_infra" = true ]; then
        init_terraform
        plan_infrastructure
        
        echo
        read -p "Do you want to proceed with infrastructure deployment? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            deploy_infrastructure
        else
            print_warning "Infrastructure deployment skipped"
            exit 0
        fi
    fi
    
    # Deploy application
    if [ "$deploy_app" = true ]; then
        build_and_push_image
        
        if [ "$run_migrations_flag" = true ]; then
            run_migrations
        fi
        
        update_ecs_service
        verify_deployment
    fi
    
    echo
    print_status "🎉 Deployment completed successfully!"
    
    # Output useful information
    echo
    print_status "📋 Deployment Summary:"
    print_status "- Environment: $ENVIRONMENT"
    print_status "- Region: $AWS_REGION"
    
    if [ "$deploy_infra" = true ]; then
        local lb_dns=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-alb --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null || echo "Not available")
        print_status "- Load Balancer: $lb_dns"
        print_status "- API URL: https://$lb_dns"
    fi
    
    print_status "- Dashboard: https://${AWS_REGION}.console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${PROJECT_NAME}-dashboard"
    
    echo
    print_status "Next steps:"
    print_status "1. Update your DNS records to point to the load balancer"
    print_status "2. Update API keys in AWS Secrets Manager"
    print_status "3. Configure monitoring alerts"
    print_status "4. Set up automated backups"
}

# Run main function with all arguments
main "$@"