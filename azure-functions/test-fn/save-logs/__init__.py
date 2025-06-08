import azure.functions as func
import os, json, logging
from datetime import datetime, timezone

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Function started - testing individual imports')

    failed_imports = []
    

    try:
        import requests
        logging.info('requests imported successfully')
    except Exception as e:
        failed_imports.append(f'requests: {str(e)}')

    try:
        from azure.identity import DefaultAzureCredential
        logging.info('azure.identity imported successfully')
    except Exception as e:
        failed_imports.append(f'azure.identity: {str(e)}')

    try:
        from azure.storage.blob import BlobServiceClient
        logging.info('azure.storage.blob imported successfully')
    except Exception as e:
        failed_imports.append(f'azure.storage.blob: {str(e)}')

    try:
        from azure.keyvault.secrets import SecretClient
        logging.info('azure.keyvault.secrets imported successfully')
    except Exception as e:
        failed_imports.append(f'azure.keyvault.secrets: {str(e)}')

    if failed_imports:
        error_msg = "Import errors:\n" + "\n".join(failed_imports)
        logging.error(error_msg)
        return func.HttpResponse(error_msg, status_code=500)

    return func.HttpResponse("All imports succeeded", status_code=200)