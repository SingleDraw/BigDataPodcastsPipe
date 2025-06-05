import logging
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient
from datetime import datetime
import json

# Read Blob Storage connection string from app settings
BLOB_CONN_STR = os.getenv("AzureWebJobsStorage")
CONTAINER_NAME = "aci-logs"

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing logs upload request.')

    # Check for function key in query params or header
    function_key = os.getenv("FUNCTION_KEY")  # your function key stored in app settings
    key_in_req = req.params.get('code') or req.headers.get('x-functions-key')
    if not key_in_req or key_in_req != function_key:
        return func.HttpResponse("Unauthorized", status_code=401)

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    aci_name = req_body.get('aciName')
    logs = req_body.get('logs')

    if not aci_name or not logs:
        return func.HttpResponse("Missing required fields", status_code=400)

    # Initialize Blob client
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    if not container_client.exists():
        container_client.create_container()

    # Create blob name with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    blob_name = f"{aci_name}/logs_{timestamp}.txt"

    # Upload logs as text blob
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(json.dumps(logs), overwrite=True)

    return func.HttpResponse(f"Logs saved to blob {blob_name}", status_code=200)
