# Azure Deployment Guide

This guide walks you through deploying the Pandemic Outbreak Tracker API to Azure using Terraform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Manual Deployment](#manual-deployment)
- [CI/CD Setup](#cicd-setup)
- [Managing Environments](#managing-environments)
- [Cost Estimation](#cost-estimation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

1. **Azure CLI** (v2.40.0 or later)
   ```bash
   # macOS
   brew install azure-cli
   
   # Verify installation
   az --version
   ```

2. **Terraform** (v1.0 or later)
   ```bash
   # macOS
   brew tap hashicorp/tap
   brew install hashicorp/tap/terraform
   
   # Verify installation
   terraform --version
   ```

3. **Docker** (v20.10 or later)
   ```bash
   # macOS
   brew install --cask docker
   
   # Verify installation
   docker --version
   ```

### Azure Account Setup

1. **Create an Azure Account**
   - Visit [Azure Portal](https://portal.azure.com)
   - Sign up for a free account (includes $200 credit)

2. **Create a Subscription**
   - If you don't have one, create a subscription in Azure Portal
   - Note your subscription ID

3. **Set Up Service Principal (for CI/CD)**
   ```bash
   # Login to Azure
   az login
   
   # Set your subscription
   az account set --subscription "<your-subscription-id>"
   
   # Create service principal
   az ad sp create-for-rbac \
     --name "pandemic-tracker-terraform" \
     --role contributor \
     --scopes /subscriptions/<your-subscription-id> \
     --sdk-auth
   ```
   
   Save the JSON output - you'll need it for GitHub Actions.

## Initial Setup

### 1. Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
project_name = "pandemic-tracker"
environment  = "dev"
location     = "Southeast Asia"

tags = {
  Project     = "Pandemic Outbreak Tracker"
  ManagedBy   = "Terraform"
  Environment = "dev"
  Owner       = "your-name"
}

# For production, adjust these
api_min_replicas = 1
api_max_replicas = 3
cors_origins     = ["*"]  # Update for production
```

### 2. Initialize Terraform

```bash
terraform init
```

This downloads the Azure provider and initializes the backend.

### 3. Validate Configuration

```bash
terraform validate
terraform fmt
```

## Manual Deployment

### Step 1: Deploy Infrastructure

```bash
cd terraform

# Preview changes
terraform plan

# Deploy
terraform apply
```

This takes approximately 5-10 minutes and creates:
- Resource Group
- Container Registry (ACR)
- Storage Account with containers
- Container Apps Environment
- Log Analytics Workspace
- Application Insights

### Step 2: Build and Push Docker Image

```bash
# Get ACR details from Terraform outputs
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
ACR_NAME=$(echo $ACR_LOGIN_SERVER | cut -d. -f1)

# Login to ACR
az acr login --name $ACR_NAME

# Build and push from project root
cd ..
docker build -t $ACR_LOGIN_SERVER/pandemic-tracker-api:latest .
docker push $ACR_LOGIN_SERVER/pandemic-tracker-api:latest
```

### Step 3: Update Container App

```bash
cd terraform

# Force Container App to pull new image
RESOURCE_GROUP=$(terraform output -raw resource_group_name)
az containerapp update \
  --name pandemic-tracker-dev-api \
  --resource-group $RESOURCE_GROUP
```

### Step 4: Upload Initial Data

```bash
STORAGE_ACCOUNT=$(terraform output -raw storage_account_name)

# Upload predictions
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination predictions \
  --source ../data/predictions/ \
  --pattern "*.json" \
  --overwrite

# Upload models
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination models \
  --source ../data/models/ \
  --pattern "*.pkl" \
  --overwrite

# Upload processed data
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination processed \
  --source ../data/processed/ \
  --pattern "*.csv" \
  --overwrite
```

### Step 5: Verify Deployment

```bash
# Get API URL
API_URL=$(terraform output -raw api_url)

# Check health endpoint
curl $API_URL/api/v1/health

# Open API documentation
open $API_URL/docs
```

## CI/CD Setup

### GitHub Actions Configuration

The project includes a GitHub Actions workflow (`.github/workflows/azure-deploy.yml`) for automated deployments.

#### Required GitHub Secrets

Navigate to your GitHub repository → Settings → Secrets → Actions, and add:

1. **AZURE_CREDENTIALS**
   ```json
   {
     "clientId": "<service-principal-client-id>",
     "clientSecret": "<service-principal-secret>",
     "subscriptionId": "<subscription-id>",
     "tenantId": "<tenant-id>"
   }
   ```
   (This is the JSON output from creating the service principal)

2. **ACR_NAME**
   ```
   pandemictrackerdevacr123abc
   ```

3. **ACR_LOGIN_SERVER**
   ```
   pandemictrackerdevacr123abc.azurecr.io
   ```

4. **STORAGE_ACCOUNT_NAME** (optional, for production data uploads)
   ```
   pandemictrackerdevdata123abc
   ```

#### Get Values for Secrets

```bash
cd terraform

# Get ACR details
terraform output -raw acr_login_server
terraform output -raw acr_login_server | cut -d. -f1

# Get storage account name
terraform output -raw storage_account_name
```

#### Trigger Deployments

**Automatic Deployment:**
Push to `main` branch automatically deploys to dev environment.

**Manual Deployment:**
1. Go to GitHub → Actions → Deploy to Azure
2. Click "Run workflow"
3. Select environment (dev/staging/production)
4. Click "Run workflow"

## Managing Environments

### Creating Multiple Environments

#### Development Environment

```bash
cd terraform
terraform apply -var="environment=dev"
```

#### Staging Environment

```bash
# Create staging tfvars
cp terraform.tfvars staging.tfvars

# Edit staging.tfvars
# environment = "staging"
# cors_origins = ["https://staging.yourdomain.com"]

# Deploy
terraform apply -var-file="staging.tfvars"
```

#### Production Environment

```bash
# Create production tfvars
cp terraform.tfvars production.tfvars

# Edit production.tfvars with production settings
# environment = "production"
# acr_sku = "Standard"
# storage_replication_type = "GRS"
# api_min_replicas = 2
# api_max_replicas = 10
# cors_origins = ["https://yourdomain.com"]

# Deploy
terraform apply -var-file="production.tfvars"
```

### Using Terraform Workspaces

Alternative approach for managing environments:

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new production

# Switch to workspace
terraform workspace select dev

# Deploy
terraform apply
```

## Cost Estimation

### Development Environment (Monthly)

- **Container Registry (Basic)**: ~$5
- **Container Apps (0.5 vCPU, 1GB RAM, 1 replica)**: ~$15-30
- **Storage Account (LRS, 10GB)**: ~$0.50
- **Log Analytics (5GB ingestion)**: ~$12
- **Application Insights**: ~$3

**Total**: ~$35-50/month

### Production Environment (Monthly)

- **Container Registry (Standard)**: ~$20
- **Container Apps (1 vCPU, 2GB RAM, 2-5 replicas)**: ~$100-200
- **Storage Account (GRS, 50GB)**: ~$5
- **Log Analytics (50GB ingestion)**: ~$120
- **Application Insights**: ~$20

**Total**: ~$265-365/month

### Cost Optimization Tips

1. **Development**: Set `api_min_replicas = 0` to scale to zero when idle
2. **Use Basic SKUs**: For non-production environments
3. **Monitor Usage**: Set up Azure Cost Management alerts
4. **Delete Unused Resources**: Run `terraform destroy` for test environments

## Monitoring and Maintenance

### View Logs

```bash
# Real-time logs
az containerapp logs show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --follow

# Query logs
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h)"
```

### View Metrics

```bash
# Container App metrics
az containerapp show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --query "properties.{replicas:configuration.activeRevisionsMode,cpu:template.containers[0].resources.cpu}"
```

### Update Application

```bash
# Build new version
docker build -t $ACR_LOGIN_SERVER/pandemic-tracker-api:v1.1 .
docker push $ACR_LOGIN_SERVER/pandemic-tracker-api:v1.1

# Update container app
az containerapp update \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --image $ACR_LOGIN_SERVER/pandemic-tracker-api:v1.1
```

### Backup Data

```bash
# Backup storage account
az storage blob download-batch \
  --account-name $STORAGE_ACCOUNT \
  --source predictions \
  --destination ./backups/predictions/

az storage blob download-batch \
  --account-name $STORAGE_ACCOUNT \
  --source models \
  --destination ./backups/models/
```

## Troubleshooting

### Container App Won't Start

**Check logs:**
```bash
az containerapp logs show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --tail 100
```

**Common issues:**
- Image not found → Check ACR image exists
- Memory errors → Increase `api_memory` in terraform.tfvars
- Python errors → Check Dockerfile and requirements.txt

### Cannot Access API

**Check ingress configuration:**
```bash
az containerapp show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --query "properties.configuration.ingress"
```

**Check if running:**
```bash
az containerapp revision list \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --query "[].{name:name,active:properties.active,replicas:properties.replicas}"
```

### Terraform Errors

**State lock errors:**
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

**Resource already exists:**
```bash
# Import existing resource
terraform import azurerm_resource_group.main /subscriptions/<sub-id>/resourceGroups/<rg-name>
```

### Storage Access Issues

**Check connection string:**
```bash
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP
```

**Test access:**
```bash
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --container-name predictions
```

## Cleanup

### Destroy Single Environment

```bash
cd terraform
terraform destroy
```

### Destroy All Resources

```bash
# List all resource groups
az group list --query "[?starts_with(name, 'pandemic-tracker')].name" -o table

# Delete specific resource group
az group delete --name pandemic-tracker-dev-rg --yes --no-wait
```

## Security Checklist

- [ ] Service principal has minimum required permissions
- [ ] Storage account keys are rotated regularly
- [ ] CORS origins are restricted in production
- [ ] Container App uses managed identity (advanced)
- [ ] Secrets are stored in Azure Key Vault (advanced)
- [ ] Network security groups configured (advanced)
- [ ] API rate limiting enabled
- [ ] HTTPS enforced (enabled by default)

## Next Steps

1. **Set up custom domain**: Configure DNS and SSL certificates
2. **Add CDN**: Use Azure CDN for static assets
3. **Implement caching**: Add Redis Cache for API responses
4. **Set up monitoring alerts**: Configure Azure Monitor alerts
5. **Implement backup strategy**: Automated backups for storage
6. **Add API Gateway**: Use Azure API Management for advanced features

## Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/)
- [FastAPI Deployment Best Practices](https://fastapi.tiangolo.com/deployment/)
