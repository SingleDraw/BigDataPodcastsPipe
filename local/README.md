
# 🔧 Setting GitHub Secrets from Local Machine

This guide describes how to configure GitHub secrets using local scripts.

## ✅ Prerequisites

Ensure the following tools are **installed and configured**:

* [GitHub CLI (`gh`)](https://cli.github.com/)
* [Azure CLI (`az`)](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
* On **Windows**, run the scripts using **Git Bash** or a compatible shell environment.

---

## 📁 Environment Setup

Before running the `init.sh` script, create a `.env` file in this directory with the following content:

```env
AZURE_SUBSCRIPTION_ID=<your-azure-subscription-id>
GITHUB_REPOSITORY=<your-github-username>/<your-repo-name>  # e.g. johndoe/myproject
```

---

## ☁️ Required Environment Variables for Terraform

Set the following environment variables to provision Azure resources correctly:

```env
TF_VAR_resource_group_name=<resource-group-name>
TF_VAR_location=westeurope
TF_VAR_storage_account_name=<globally-unique-storage-account-name>
TF_VAR_container_registry_name=<acr-name>
TF_VAR_container_app_environment_name=<container-app-env-name>
```

> 🔒 **Note:** `TF_VAR_storage_account_name` must be **globally unique** across all Azure accounts.
> The other values (e.g., resource group, ACR name) should be unique **within your subscription** to avoid naming conflicts.



## NEXT: Run bootstrap.sh for provisioning resource group, storage, storage containers and terraform backend configuration.
# provision.sh runs in chaing afterwards
Do it once. (but its indempotent anyway)

## Subsequent rebuilds of main infra should be done by provision.sh

## Build and push workflows checks if infra is ready using env var set in github repo 
