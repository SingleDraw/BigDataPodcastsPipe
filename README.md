
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