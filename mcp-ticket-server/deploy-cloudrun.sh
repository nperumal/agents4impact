#!/bin/bash

# MCP Ticket Server - Cloud Run Deployment Script
# This script builds and deploys the MCP Ticket Server to GCP Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_info "Checking requirements..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    print_success "All requirements met"
}

# Configuration
echo ""
echo "======================================"
echo "  MCP Ticket Server Cloud Run Deploy"
echo "======================================"
echo ""

# Check requirements
check_requirements

# Get configuration
read -p "Enter GCP Project ID: " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID is required"
    exit 1
fi

read -p "Enter Region [us-central1]: " REGION
REGION=${REGION:-us-central1}

read -p "Enter Service Name [mcp-ticket-server]: " SERVICE_NAME
SERVICE_NAME=${SERVICE_NAME:-mcp-ticket-server}

read -p "Use Artifact Registry? (y/n) [y]: " USE_AR
USE_AR=${USE_AR:-y}

# Set image name based on registry choice
if [[ "$USE_AR" =~ ^[Yy]$ ]]; then
    read -p "Enter Artifact Registry Repository Name [mcp-servers]: " REPO_NAME
    REPO_NAME=${REPO_NAME:-mcp-servers}
    IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME"
    print_info "Using Artifact Registry: $IMAGE_NAME"
else
    IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
    print_info "Using Container Registry: $IMAGE_NAME"
fi

echo ""
print_info "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image: $IMAGE_NAME:latest"
echo ""

read -p "Continue with deployment? (y/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

echo ""
print_info "Starting deployment..."
echo ""

# Set GCP project
print_info "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Create Artifact Registry repository if needed
if [[ "$USE_AR" =~ ^[Yy]$ ]]; then
    print_info "Checking Artifact Registry repository..."
    if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION &> /dev/null; then
        print_info "Creating Artifact Registry repository..."
        gcloud artifacts repositories create $REPO_NAME \
            --repository-format=docker \
            --location=$REGION \
            --description="MCP Servers Repository" \
            --project=$PROJECT_ID
        print_success "Repository created"
    else
        print_success "Repository already exists"
    fi
    
    # Configure Docker auth
    print_info "Configuring Docker authentication..."
    gcloud auth configure-docker $REGION-docker.pkg.dev --quiet
fi

# Build Docker image
print_info "Building Docker image..."
docker build -t $IMAGE_NAME:latest .
print_success "Docker image built successfully"

# Test image locally (optional)
read -p "Test image locally before pushing? (y/n) [n]: " TEST_LOCAL
if [[ "$TEST_LOCAL" =~ ^[Yy]$ ]]; then
    print_info "Starting container locally on port 3000..."
    docker run -d -p 3000:3000 -e PORT=3000 --name mcp-test $IMAGE_NAME:latest
    sleep 5
    
    print_info "Testing health endpoint..."
    if curl -s http://localhost:3000/health > /dev/null; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        docker stop mcp-test && docker rm mcp-test
        exit 1
    fi
    
    docker stop mcp-test && docker rm mcp-test
    print_success "Local test completed"
fi

# Push Docker image
print_info "Pushing Docker image to registry..."
docker push $IMAGE_NAME:latest
print_success "Image pushed successfully"

# Deploy to Cloud Run
print_info "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 3000 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80 \
    --project $PROJECT_ID \
    --quiet

print_success "Deployment completed!"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)')

echo ""
echo "======================================"
echo "  Deployment Successful! 🎉"
echo "======================================"
echo ""
echo "Service URL: $SERVICE_URL"
echo ""
print_info "Testing deployed service..."

# Test health endpoint
if curl -s "$SERVICE_URL/health" > /dev/null; then
    print_success "Service is responding correctly"
    echo ""
    echo "Health Check: $SERVICE_URL/health"
    echo "List Events: $SERVICE_URL/mcp/tool/list_events"
    echo "Get Balance: $SERVICE_URL/mcp/tool/get_balance"
else
    print_warning "Service is deployed but health check failed"
    print_info "Check logs: gcloud run services logs read $SERVICE_NAME --region $REGION"
fi

echo ""
print_info "View logs:"
echo "  gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
print_info "View service details:"
echo "  gcloud run services describe $SERVICE_NAME --region $REGION"
echo ""
print_info "Update environment variables:"
echo "  gcloud run services update $SERVICE_NAME --region $REGION --set-env-vars KEY=VALUE"
echo ""

print_success "Done!"
