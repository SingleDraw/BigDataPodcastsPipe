import azure.functions as func
import os, json, logging
from datetime import datetime, timezone

# from azure.identity import DefaultAzureCredential
# from azure.storage.blob import BlobServiceClient
# from azure.keyvault.secrets import SecretClient
# from azure.core.exceptions import ResourceExistsError
# from typing import Optional



# # Read environment variables
# AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")
# KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL", "")
# KEY_VAULT_SECRET_NAME = os.getenv("AZURE_KEY_VAULT_SECRET_NAME")
# CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "aci-logs")
# FUNCTION_KEY = os.getenv("FUNCTION_KEY")


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Function started - basic imports work')
    
    try:
        import requests
        from azure.identity import DefaultAzureCredential
        logging.info('azure.identity imported successfully')
        return func.HttpResponse("Success", status_code=200)
    except Exception as e:
        logging.error(f'Import failed: {str(e)}')
        return func.HttpResponse(
            f"Import error: {str(e)}", 
            status_code=500
        )