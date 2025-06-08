import os, json, logging
from datetime import datetime, timezone
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import ResourceExistsError
# from typing import Optional



# # Read environment variables
# AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")
# KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL", "")
# KEY_VAULT_SECRET_NAME = os.getenv("AZURE_KEY_VAULT_SECRET_NAME")
# CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "aci-logs")
# FUNCTION_KEY = os.getenv("FUNCTION_KEY")


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        # Simple test response
        return func.HttpResponse(
            "Hello! Function is working correctly.",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
