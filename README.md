
## ✅ 1. Generate Azure Credentials JSON file

Using AzureCLI and subscription id generate credentials file:
```bash
az ad sp create-for-rbac --name "gha-terraform" --role="Contributor" --scopes="/subscriptions/<your-subscription-id>" --sdk-auth
```
It creates file azure-credentials.json, which content will be needed for github actions.

---

### ✅ 2. **Create GitHub Secret**

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → click **New repository secret**.

Name it:

```plaintext
AZURE_CREDENTIALS
```

Paste the **entire contents** of your `azure-credentials.json`.

or run usin GitHubCLI (gh):

```bash
gh secret set AZURE_CREDENTIALS --body '{"clientId":"<your-client-id>","clientSecret":"<your-client-secret>","subscriptionId":"<your-subscription-id>","tenantId":"<your-tenant-id>"}'
```



### or run from your local machine init.sh with propely populated .env file (read REAMDE from local directory)
## GitHub Token (Required for setting other secrets):
- `GH_PAT_TOKEN` - GitHub Personal Access Token with repo and admin:repo_hook permissions

## How to create GitHub Personal Access Token:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `admin:repo_hook` (Admin repo hooks)
4. Copy the token and add it as `GH_PAT_TOKEN` secret and paste it in .env file




📁 Project structure:
```bash
/infra/                     # Infra: ACR, Container Apps, Storage, etc.
/docker/ingest/             # Dockerfile + code for ingest stage
/docker/process/            # Dockerfile + code for processing
/docker/export/             # Dockerfile + code for export/output
/app/                       # Shared libs or CLI code
.github/workflows/          # GitHub Actions CI/CD workflows
README.md
```



