# GitHub Repository Secrets Setup

Go to your GitHub repository → Settings → Secrets and variables → Actions

## Required Secrets for Azure Authentication:

### `AZURE_CLIENT_ID`
- Your Azure Service Principal Application ID
- Get from: `az ad sp show --id <your-sp-id> --query appId -o tsv`

### `AZURE_CLIENT_SECRET` 
- Your Azure Service Principal password/secret
- Created when you create the service principal

### `AZURE_SUBSCRIPTION_ID`
- Your Azure subscription ID
- Get from: `az account show --query id -o tsv`

### `AZURE_TENANT_ID`
- Your Azure tenant ID  
- Get from: `az account show --query tenantId -o tsv`

## How to create Azure Service Principal:

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "github-actions-sp" \
  --role "Contributor" \
  --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID" \
  --sdk-auth

# This outputs JSON with all the values you need for GitHub secrets
```

## Alternative: Using Azure CLI to set secrets automatically

```bash
# If you have GitHub CLI installed
gh secret set AZURE_CLIENT_ID --body "your-client-id"
gh secret set AZURE_CLIENT_SECRET --body "your-client-secret"  
gh secret set AZURE_SUBSCRIPTION_ID --body "your-subscription-id"
gh secret set AZURE_TENANT_ID --body "your-tenant-id"
```

## Why this approach works:

1. **Terraform provisions** ACR and outputs credentials
2. **GitHub Actions reads** those outputs 
3. **Docker login** uses the credentials to authenticate
4. **Docker push** uploads your built image to ACR
5. **Deployment step** can use the new image