# Terraform Quick Start Guide

One-page reference for deploying to Azure.

## Prerequisites

```bash
# Install tools (macOS)
brew install azure-cli terraform docker

# Login to Azure
az login
az account set --subscription "<your-subscription-id>"
```

## First Time Setup

```bash
# 1. Configure variables
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings

# 2. Initialize Terraform
terraform init

# 3. Deploy infrastructure
terraform apply
```

## Build & Deploy

```bash
# Get ACR details
ACR_LOGIN_SERVER=$(terraform output -raw acr_login_server)
ACR_NAME=$(echo $ACR_LOGIN_SERVER | cut -d. -f1)

# Login and push
az acr login --name $ACR_NAME
cd ..
docker build -t $ACR_LOGIN_SERVER/pandemic-tracker-api:latest .
docker push $ACR_LOGIN_SERVER/pandemic-tracker-api:latest

# Update container app
cd terraform
az containerapp update \
  --name pandemic-tracker-dev-api \
  --resource-group $(terraform output -raw resource_group_name)
```

## Upload Data

```bash
STORAGE_ACCOUNT=$(terraform output -raw storage_account_name)

# Upload predictions
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination predictions \
  --source ../data/predictions/ \
  --overwrite

# Upload models
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination models \
  --source ../data/models/ \
  --overwrite
```

## Common Commands

```bash
# View outputs
terraform output
terraform output -raw api_url

# View logs
az containerapp logs show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --follow

# Restart app
az containerapp revision restart \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg

# List revisions
az containerapp revision list \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg

# Update infrastructure
terraform plan
terraform apply

# Destroy everything
terraform destroy
```

## Verify Deployment

```bash
# Get API URL
API_URL=$(terraform output -raw api_url)

# Test endpoints
curl $API_URL/api/v1/health
curl $API_URL/api/v1/locations
curl $API_URL/api/v1/predictions

# Open docs
open $API_URL/docs
```

## GitHub Actions Secrets

Add these to GitHub → Settings → Secrets:

1. **AZURE_CREDENTIALS** - Service principal JSON
2. **ACR_NAME** - Container registry name
3. **ACR_LOGIN_SERVER** - Container registry URL
4. **STORAGE_ACCOUNT_NAME** - Storage account name

Get values:
```bash
terraform output -raw acr_login_server
terraform output -raw acr_login_server | cut -d. -f1
terraform output -raw storage_account_name
```

## Troubleshooting

### Can't access API
```bash
az containerapp show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --query "properties.configuration.ingress"
```

### Container won't start
```bash
az containerapp logs show \
  --name pandemic-tracker-dev-api \
  --resource-group pandemic-tracker-dev-rg \
  --tail 100
```

### ACR login fails
```bash
az acr credential show --name <acr-name>
```

## Estimated Costs

**Development**: ~$35-50/month
**Production**: ~$265-365/month

Use `api_min_replicas = 0` in dev to reduce costs.

## Architecture

```
Internet
   ↓
Container App (FastAPI)
   ↓
Storage Account
   ├── models/       (trained ML models)
   ├── predictions/  (JSON predictions)
   ├── processed/    (processed CSV data)
   └── raw/          (raw data)
```

## Key Files

- `terraform/main.tf` - Infrastructure definition
- `terraform/variables.tf` - Configuration variables
- `terraform/outputs.tf` - Output values
- `Dockerfile` - Container image definition
- `.github/workflows/azure-deploy.yml` - CI/CD pipeline

## Support

Full documentation: `terraform/README.md`
Deployment guide: `docs/AZURE_DEPLOYMENT.md`
