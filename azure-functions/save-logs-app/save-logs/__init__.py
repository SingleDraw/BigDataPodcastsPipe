import logging
import azure.functions as func


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

# import os, json, logging
# from datetime import datetime, timezone
# import azure.functions as func
# from azure.identity import DefaultAzureCredential
# from azure.storage.blob import BlobServiceClient
# from azure.keyvault.secrets import SecretClient
# from azure.core.exceptions import ResourceExistsError
# from typing import Optional


# def get_blob_service_client(
#         storage_account: Optional[str] = None,
#         key_vault_url: Optional[str] = None,
#         key_vault_secret_name: Optional[str] = None
#     ) -> BlobServiceClient:
#     """
#     Initializes and returns a BlobServiceClient 
#     using the connection string from environment variables.
#     Uses DefaultAzureCredential for authentication if no connection string is provided.
#     """
#     # Fixed logic: if we have key vault info, use it
#     if key_vault_url and key_vault_secret_name:
#         credential = DefaultAzureCredential()
#         secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
#         conn_str = secret_client.get_secret(key_vault_secret_name).value
#         return BlobServiceClient.from_connection_string(conn_str)
#     elif storage_account:
#         credential = DefaultAzureCredential()
#         account_url = f"https://{storage_account}.blob.core.windows.net"
#         return BlobServiceClient(
#             account_url=account_url, 
#             credential=credential
#         )
#     else:
#         raise ValueError(
#             "Either storage_account or key_vault_url "
#             "and key_vault_secret_name must be provided."
#         )


# # Read environment variables
# AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")
# KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL", "")
# KEY_VAULT_SECRET_NAME = os.getenv("AZURE_KEY_VAULT_SECRET_NAME")
# CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "aci-logs")
# FUNCTION_KEY = os.getenv("FUNCTION_KEY")


# def main(req: func.HttpRequest) -> func.HttpResponse:
#     logging.info('Processing logs upload request.')

#     # Check for function key in query params or header
#     key_in_req = req.params.get('code') or req.headers.get('x-functions-key')

#     if not key_in_req or key_in_req != FUNCTION_KEY:
#         return func.HttpResponse("Unauthorized", status_code=401)

#     try:
#         req_body = req.get_json()
#     except ValueError:
#         return func.HttpResponse("Invalid JSON", status_code=400)

#     aci_name = req_body.get('aciName')
#     logs = req_body.get('logs')

#     if not aci_name or not logs:
#         return func.HttpResponse("Missing required fields", status_code=400)

#     # Initialize Blob client
#     blob_service_client = get_blob_service_client(
#         storage_account=AZURE_STORAGE_ACCOUNT,
#         key_vault_url=KEY_VAULT_URL,
#         key_vault_secret_name=KEY_VAULT_SECRET_NAME
#     )

#     container_client = blob_service_client.get_container_client(
#         CONTAINER_NAME
#     )

#     if not container_client.exists():
#         # Create container if it does not exist
#         # This will raise ResourceExistsError if it already exists
#         # It's a good practice to handle this exception
#         # when creating containers in case of concurrent requests
#         # not really needed in this case, but as a good practice
#         try:
#             container_client.create_container()
#         except ResourceExistsError:
#             pass  # Already exists, continue

#     # Create blob name with timestamp
#     timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d--%H-%M-%S')
#     blob_name = f"{aci_name}_logs/{timestamp}.txt"

#     # Upload logs as text blob
#     blob_client = container_client.get_blob_client(blob_name)
#     blob_client.upload_blob(json.dumps(logs), overwrite=True)

#     return func.HttpResponse(f"Logs saved to blob {blob_name}", status_code=200)

