# GCP Cloud Run Deployment Guide for MCP Ticket Server

## Prerequisites

1. **Google Cloud SDK** installed and configured
   ```bash
   gcloud --version
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Docker** installed
   ```bash
   docker --version
   ```

3. **GCP Project** with billing enabled
   - Cloud Run API enabled
   - Artifact Registry API enabled (or Container Registry)

## Quick Deploy to Cloud Run

### Option 1: Direct Deploy (Recommended)

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="mcp-ticket-server"

# Deploy directly from source
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 3000 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --project $PROJECT_ID
```

### Option 2: Build and Push Docker Image

```bash
# Set variables
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="mcp-ticket-server"
export IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build Docker image
docker build -t $IMAGE_NAME:latest .

# Test locally (optional)
docker run -p 3000:3000 -e PORT=3000 $IMAGE_NAME:latest

# Push to Google Container Registry
docker push $IMAGE_NAME:latest

# Deploy to Cloud Run
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
  --project $PROJECT_ID
```

### Option 3: Using Artifact Registry (Recommended for Production)

```bash
# Set variables
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export SERVICE_NAME="mcp-ticket-server"
export REPO_NAME="mcp-servers"
export IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME"

# Create Artifact Registry repository (first time only)
gcloud artifacts repositories create $REPO_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="MCP Servers Repository" \
  --project=$PROJECT_ID

# Configure Docker auth
gcloud auth configure-docker $REGION-docker.pkg.dev

# Build and tag image
docker build -t $IMAGE_NAME:latest .

# Push to Artifact Registry
docker push $IMAGE_NAME:latest

# Deploy to Cloud Run
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
  --project $PROJECT_ID
```

## Environment Variables

Set environment variables in Cloud Run:

```bash
# Set environment variables
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars "NODE_ENV=production,BASE_SEPOLIA_RPC=https://sepolia.base.org" \
  --project $PROJECT_ID

# Set secrets (for sensitive data like private keys)
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-secrets "PAYMENT_WALLET_PRIVATE_KEY=wallet-key:latest" \
  --project $PROJECT_ID
```

## Cloud Run Configuration

### Recommended Settings

| Setting | Value | Description |
|---------|-------|-------------|
| **CPU** | 1 | Single vCPU sufficient for most workloads |
| **Memory** | 512Mi | Adequate for Node.js + blockchain RPC |
| **Min Instances** | 0 | Scale to zero when not in use |
| **Max Instances** | 10 | Handle traffic spikes |
| **Timeout** | 300s | Allow time for blockchain operations |
| **Port** | 3000 | Express server port |
| **Concurrency** | 80 | Requests per container |

### Autoscaling Configuration

```bash
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 80 \
  --cpu-throttling \
  --project $PROJECT_ID
```

## Local Testing

### Build Docker Image Locally

```bash
docker build -t mcp-ticket-server:test .
```

### Run Locally

```bash
# Run with default settings
docker run -p 3000:3000 \
  -e PORT=3000 \
  mcp-ticket-server:test

# Run with environment variables
docker run -p 3000:3000 \
  -e PORT=3000 \
  -e BASE_SEPOLIA_RPC=https://sepolia.base.org \
  -e PAYMENT_WALLET_PRIVATE_KEY=your_private_key \
  mcp-ticket-server:test
```

### Test the Container

```bash
# Health check
curl http://localhost:3000/health

# List events
curl -X POST http://localhost:3000/mcp/tool/list_events \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Checklist

### Before Deployment

- [ ] Set production environment variables
- [ ] Configure wallet private key as secret
- [ ] Set up custom domain (optional)
- [ ] Configure Cloud Armor for DDoS protection
- [ ] Set up Cloud Logging and Monitoring
- [ ] Configure VPC connector (if needed for private resources)
- [ ] Test locally with Docker
- [ ] Review resource limits

### After Deployment

- [ ] Test all endpoints
- [ ] Verify health checks
- [ ] Check logs for errors
- [ ] Monitor performance metrics
- [ ] Test autoscaling behavior
- [ ] Verify CORS settings
- [ ] Test blockchain connectivity

## Monitoring and Logging

### View Logs

```bash
# Stream logs
gcloud run services logs tail $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID

# View recent logs
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --limit 50 \
  --project $PROJECT_ID
```

### Monitor Metrics

```bash
# Get service details
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID
```

## Troubleshooting

### Container Fails to Start

1. Check logs:
   ```bash
   gcloud run services logs read $SERVICE_NAME --region $REGION --limit 100
   ```

2. Verify build locally:
   ```bash
   docker build -t test .
   docker run -p 3000:3000 test
   ```

### Health Check Failing

1. Test locally:
   ```bash
   curl http://localhost:3000/health
   ```

2. Check PORT environment variable is set correctly

### Out of Memory

1. Increase memory allocation:
   ```bash
   gcloud run services update $SERVICE_NAME \
     --region $REGION \
     --memory 1Gi
   ```

### Timeout Issues

1. Increase timeout:
   ```bash
   gcloud run services update $SERVICE_NAME \
     --region $REGION \
     --timeout 600
   ```

## Cost Optimization

### Estimated Costs

- **Free Tier**: 2 million requests/month, 360,000 vCPU-seconds/month
- **Paid Tier**: ~$0.10 per million requests + compute time
- **Idle Cost**: $0 (with min-instances=0)

### Cost Reduction Tips

1. Set `min-instances=0` to scale to zero
2. Use appropriate memory allocation (512Mi recommended)
3. Optimize cold start time
4. Use request-based pricing
5. Monitor and adjust concurrency settings

## Security

### Best Practices

1. **Use Secrets Manager** for sensitive data:
   ```bash
   # Create secret
   echo -n "your_private_key" | gcloud secrets create wallet-key --data-file=-
   
   # Grant access to Cloud Run service account
   gcloud secrets add-iam-policy-binding wallet-key \
     --member="serviceAccount:YOUR_SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

2. **Configure IAM** properly:
   ```bash
   # Allow only authenticated users
   gcloud run services remove-iam-policy-binding $SERVICE_NAME \
     --member="allUsers" \
     --role="roles/run.invoker" \
     --region=$REGION
   ```

3. **Enable Cloud Armor** for DDoS protection

4. **Use Custom Service Account** with minimal permissions

5. **Enable VPC connector** for private resource access

## CI/CD Integration

### GitHub Actions Example

See `.github/workflows/deploy-cloudrun.yml` in the repository.

### Cloud Build

```bash
# Submit build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --region $REGION
```

## Custom Domain

### Map Custom Domain

```bash
# Map domain
gcloud run domain-mappings create \
  --service $SERVICE_NAME \
  --domain api.yourdomain.com \
  --region $REGION
```

## Useful Commands

```bash
# Get service URL
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format='value(status.url)'

# Update service
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --memory 1Gi

# Delete service
gcloud run services delete $SERVICE_NAME \
  --region $REGION

# List all services
gcloud run services list --project $PROJECT_ID

# Describe service
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format=json
```

## Next Steps

1. Deploy to Cloud Run
2. Test all endpoints
3. Set up monitoring and alerts
4. Configure custom domain
5. Integrate with CI/CD
6. Set up staging environment
7. Configure backup and disaster recovery

## Support

- **Documentation**: See README.md and COMPLETE_SUCCESS.md
- **Logs**: Use `gcloud run services logs`
- **Monitoring**: Cloud Console > Cloud Run > Your Service
- **Issues**: Check TROUBLESHOOTING.md

---

**Last Updated:** October 26, 2025  
**Status:** Production Ready ✅
