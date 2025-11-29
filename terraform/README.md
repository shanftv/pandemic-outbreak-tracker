# Terraform Configuration for Pandemic Outbreak Tracker

This directory contains Terraform configuration for deploying the Pandemic Outbreak Tracker API to Azure.

## Architecture Overview

The deployment creates the following Azure resources:

- **Resource Group**: Container for all resources
- **Azure Container Registry (ACR)**: Stores Docker images
- **Azure Container Apps**: Hosts the FastAPI application with auto-scaling
- **Azure Storage Account**: Stores models, predictions, and processed data
- **Log Analytics Workspace**: Centralized logging
- **Application Insights**: Application monitoring and telemetry

## Prerequisites

1. **Azure CLI** - [Install Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
   ```bash
   az --version
   ```

2. **Terraform** - [Install Terraform](https://www.terraform.io/downloads)
   ```bash
   terraform --version
   ```

3. **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
   ```bash
   docker --version
   ```

4. **Azure Subscription** - You need an active Azure subscription

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Configure Variables

Copy the example variables file and customize:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your preferences:
- Change `project_name` if desired
- Set `environment` (dev, staging, or production)
- Choose Azure `location` (e.g., "Southeast Asia")
- Configure CORS origins for production

### 3. Initialize Terraform

```bash
terraform init
```

This downloads required providers and initializes the backend.

### 4. Plan Deployment

```bash
terraform plan
```

Review the resources that will be created.

### 5. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. Deployment takes ~5-10 minutes.

### 6. Build and Push Docker Image

After Terraform completes, it will output the ACR login server. Use it to build and push:

```bash
# Get ACR credentials
ACR_NAME=$(terraform output -raw acr_login_server | cut -d. -f1)
az acr login --name $ACR_NAME

# Build and push from project root
cd ..
docker build -t $(terraform output -raw acr_login_server)/pandemic-tracker-api:latest .
docker push $(terraform output -raw acr_login_server)/pandemic-tracker-api:latest
```

### 7. Update Container App

After pushing the image, trigger a new revision:

```bash
cd terraform
az containerapp update \
  --name pandemic-tracker-dev-api \
  --resource-group $(terraform output -raw resource_group_name)
```

### 8. Upload Data to Storage

Upload your trained models and predictions:

```bash
STORAGE_ACCOUNT=$(terraform output -raw storage_account_name)

# Upload predictions
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination predictions \
  --source ../data/predictions/ \
  --pattern "*.json"

# Upload models
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination models \
  --source ../data/models/ \
  --pattern "*.pkl"

# Upload processed data
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination processed \
  --source ../data/processed/ \
  --pattern "*.csv"
```

### 9. Access Your API

```bash
terraform output api_url
```

Visit the URL to access your API. Add `/docs` for Swagger documentation.

## Outputs

After deployment, Terraform provides these outputs:

- `api_url` - Public URL of the API
- `acr_login_server` - Container registry URL
- `storage_account_name` - Storage account name
- `deployment_instructions` - Step-by-step deployment guide

View all outputs:
```bash
terraform output
```

View sensitive outputs:
```bash
terraform output -raw acr_admin_password
terraform output -raw storage_primary_access_key
```

## Configuration Options

### Environment Variables

The Container App automatically configures these environment variables:

- `PANDEMIC_API_DEBUG` - Set based on environment
- `PANDEMIC_API_CORS_ORIGINS` - CORS allowed origins
- `AZURE_STORAGE_CONNECTION_STRING` - Storage connection (secret)
- `AZURE_STORAGE_ACCOUNT_NAME` - Storage account name

### Scaling

Configure auto-scaling in `variables.tf`:

```hcl
api_min_replicas = 1  # Minimum instances
api_max_replicas = 3  # Maximum instances
```

Container Apps will auto-scale based on HTTP traffic.

### Resources

Adjust CPU and memory in `terraform.tfvars`:

```hcl
api_cpu    = 0.5    # CPU cores
api_memory = "1Gi"  # Memory
```

## Monitoring

### View Logs

```bash
# Follow live logs
az containerapp logs show \
  --name pandemic-tracker-dev-api \
  --resource-group $(terraform output -raw resource_group_name) \
  --follow

# View Application Insights
az monitor app-insights component show \
  --app pandemic-tracker-dev-insights \
  --resource-group $(terraform output -raw resource_group_name)
```

### Metrics

Access metrics in Azure Portal:
1. Navigate to Container Apps
2. Select your app
3. View "Metrics" and "Log stream"

## Updating the Deployment

### Update Application Code

1. Make code changes
2. Build new Docker image with updated tag
3. Push to ACR
4. Update Container App

```bash
# Build with new tag
docker build -t $ACR_LOGIN_SERVER/pandemic-tracker-api:v1.1 .
docker push $ACR_LOGIN_SERVER/pandemic-tracker-api:v1.1

# Update terraform.tfvars
# api_image_tag = "v1.1"

# Apply changes
terraform apply
```

### Update Infrastructure

Modify Terraform files, then:

```bash
terraform plan   # Review changes
terraform apply  # Apply changes
```

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Build and Push Docker Image
        run: |
          az acr login --name ${{ secrets.ACR_NAME }}
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/pandemic-tracker-api:${{ github.sha }} .
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/pandemic-tracker-api:${{ github.sha }}
      
      - name: Update Container App
        run: |
          az containerapp update \
            --name pandemic-tracker-prod-api \
            --resource-group pandemic-tracker-prod-rg \
            --image ${{ secrets.ACR_LOGIN_SERVER }}/pandemic-tracker-api:${{ github.sha }}
```

## Cost Optimization

### Development Environment

- Use `Basic` ACR SKU
- Use `LRS` storage replication
- Set `api_min_replicas = 0` (scale to zero when idle)
- Lower log retention days

### Production Environment

- Consider `Standard` or `Premium` ACR for geo-replication
- Use `GRS` or `RAGRS` storage for redundancy
- Increase `api_min_replicas` for availability
- Enable Application Insights continuous export

## Troubleshooting

### Container App Not Starting

Check logs:
```bash
az containerapp logs show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --follow
```

### Image Pull Errors

Verify ACR credentials:
```bash
az acr credential show --name <acr-name>
```

### Storage Access Issues

Check connection string:
```bash
az storage account show-connection-string \
  --name <storage-account-name> \
  --resource-group <resource-group-name>
```

### API Health Check Failing

Test locally first:
```bash
docker run -p 8000:8000 <image-name>
curl http://localhost:8000/api/v1/health
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

Type `yes` when prompted. This will delete:
- All Azure resources
- Container images in ACR
- Data in storage account

**Warning**: This is irreversible. Backup data before destroying.

## Security Best Practices

1. **Secrets Management**: Never commit `terraform.tfvars` with sensitive data
2. **Storage Keys**: Rotate storage account keys regularly
3. **ACR Authentication**: Use managed identities in production
4. **CORS**: Restrict origins to specific domains in production
5. **Network Security**: Consider VNet integration for production
6. **RBAC**: Use Azure RBAC for access control

## Advanced Configuration

### Remote State Management

For team collaboration, use Azure Storage for Terraform state:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstate<unique>"
    container_name       = "tfstate"
    key                  = "pandemic-tracker.tfstate"
  }
}
```

### Custom Domain

To add a custom domain:

1. Add DNS CNAME record pointing to Container App FQDN
2. Configure custom domain in Azure Portal
3. Enable managed certificate

### Multi-Environment Setup

Use Terraform workspaces:

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new production

# Switch workspace
terraform workspace select production

# Deploy
terraform apply -var-file="production.tfvars"
```

## Support

For issues:
1. Check Azure Container Apps documentation
2. Review Terraform Azure provider docs
3. Check application logs in Log Analytics
4. Review Application Insights telemetry

## Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/)
- [Application Insights Documentation](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
