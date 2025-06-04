# GitHub Secrets You Need to Set Manually (One Time)

## Azure Authentication (Required for Terraform):
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET` 
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_TENANT_ID`

## GitHub Token (Required for setting other secrets):
- `GH_PAT_TOKEN` - GitHub Personal Access Token with repo and admin:repo_hook permissions

## How to create GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `admin:repo_hook` (Admin repo hooks)
4. Copy the token and add it as `GH_PAT_TOKEN` secret

## After this setup:
- Terraform will automatically create all other secrets:
  - `ACR_LOGIN_SERVER`
  - `ACR_USERNAME` 
  - `ACR_PASSWORD`
  - `AZURE_RESOURCE_GROUP`
  - `KEY_VAULT_NAME`
  - `STORAGE_ACCOUNT_NAME`

## Verification:
After running Terraform, check your GitHub repo → Settings → Secrets and variables → Actions
You should see all the auto-generated secrets there.