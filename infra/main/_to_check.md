 2025-06-02T13:10:54.188Z [WARN]  Provider "registry.terraform.io/hashicorp/azurerm" produced an invalid plan for azurerm_key_vault.kv, but we are tolerating it because it is using the legacy plugin SDK.
    The following problems may be the cause of any confusing errors from downstream operations:
      - .enable_rbac_authorization: planned value cty.False for a non-computed attribute
      - .public_network_access_enabled: planned value cty.True for a non-computed attribute
      - .soft_delete_retention_days: planned value cty.NumberIntVal(90) for a non-computed attribute
      - .enabled_for_deployment: planned value cty.False for a non-computed attribute
      - .enabled_for_disk_encryption: planned value cty.False for a non-computed attribute
      - .tags: planned value cty.MapValEmpty(cty.String) for a non-computed attribute
      - .enabled_for_template_deployment: planned value cty.False for a non-computed attribute
      - .purge_protection_enabled: planned value cty.False for a non-computed attribute
      - .network_acls: block count in plan (1) disagrees with count in config (0)



      This error confirms: **Terraform state doesn’t know about these existing Key Vault secrets**, but you declared them in config — so Terraform tries to create them and fails because they already exist.

### Your options:

#### ✅ Option 1: Import them

```bash
terraform import azurerm_key_vault_secret.acr_username "https://.../secrets/acr-admin-username"
terraform import azurerm_key_vault_secret.blob_connection_string "https://.../secrets/blob-storage-connection-string"
```

> Do this once to align real Azure resources with your Terraform state.

#### 🔁 Option 2: Remove from config temporarily

If you're not ready to manage them with Terraform yet, just comment out or delete the related `resource` blocks.

---

### Summary:

Yes, imports are **required** if the state backend exists but doesn't yet include a particular resource that **already exists in Azure**. Terraform needs state-awareness to manage it.
