import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from app.src.logging_config import logger
from app.src.storage.errors import StorageDownloadError, StorageUploadError
from typing import IO, Optional
from app.src.utils import Validate
from io import BytesIO

class AzureBlobStorageClient:

    def __init__(
        self, 
        azure_storage_account: Optional[str],
        azure_storage_key: Optional[str],
        azure_storage_connection_string: Optional[str]
    ):
        Validate.non_empty_string(azure_storage_account, "azure_storage_account")

        if azure_storage_connection_string:
            """
            Use connection string for authentication.
            """
            self.blob_service_client = BlobServiceClient.from_connection_string(
                azure_storage_connection_string
            )
        elif azure_storage_account and azure_storage_key:
            """
            Build connection string for authentication.
            """
            connection_string = (
                "DefaultEndpointsProtocol=https;"
                f"AccountName={azure_storage_account};"
                f"AccountKey={azure_storage_key};"
                "EndpointSuffix=core.windows.net"
            )
        
            self.blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
        elif azure_storage_account:
            """
            Use DefaultAzureCredential for authentication.
            """
            credential = DefaultAzureCredential()
            try:
                # Get a token for the Azure Storage service
                # This is necessary to ensure the credential is valid and raises an error if not
                # Otherwise it wont exit the program if the credential is invalid
                _ = credential.get_token("https://storage.azure.com/.default")
            except Exception as e:
                raise ValueError(f"Failed to get Azure token: {e}")

            self.blob_service_client = BlobServiceClient(
                account_url=f"https://{azure_storage_account}.blob.core.windows.net",
                credential=credential
            )
        else:
            raise ValueError(
                "Azure Storage Account and Key must be provided for string based authentication."
                "Or at least Azure Storage Account for DefaultAzureCredential."
            )



    # def storage_unit_exists(self, container_name: str) -> bool:
    #     try:
    #         container_client = self.blob_service_client.get_container_client(container_name)
    #         return container_client.exists()
    #     except Exception as e:
    #         print(f"Error checking existence of container '{container_name}': {e}")
    #         return False



    # def create_storage_unit(self, container_name: str):
    #     try:
    #         container_client = self.blob_service_client.get_container_client(container_name)
    #         container_client.create_container()
    #         print(f"Container '{container_name}' created successfully.")
    #     except Exception as e:
    #         print(f"Error creating container '{container_name}': {e}")
    #         raise Exception(f"Failed to create container '{container_name}': {e}")



    # def list_storage_units(self):
    #     try:
    #         containers = self.blob_service_client.list_containers()
    #         print("Azure Blob Containers:")
    #         for container in containers:
    #             print(f"  - {container['name']}")
    #     except Exception as e:
    #         print(f"Error listing Azure Blob containers: {e}")



    # def upload_file(
    #     self, 
    #     storage_unit: str, 
    #     source_path: str, 
    #     storage_path: str
    # ):

    def upload_file(
            self, 
            source: BytesIO | str,
            storage_key: str, 
            container_name: Optional[str], 
            overwrite: bool = True
        ) -> None:
        """
        Upload a blob to Azure Blob Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")

        if isinstance(source, str):
            # If data is a string, treat it as a local file path
            if not os.path.exists(source):
                raise FileNotFoundError(f"Local file {source} does not exist.")
            with open(source, "rb") as f:
                _data = BytesIO(f.read())

        elif isinstance(source, BytesIO):
            _data = source
        else:
            raise TypeError("Data must be a BytesIO object or a local file path string.")

        Validate.is_instance(_data, BytesIO, "data")

        try:
            container_name = container_name or self.container_name
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=storage_key
            )

            if not blob_client.exists() or overwrite:
                _data.seek(0)  # Reset pointer for proper read
                blob_client.upload_blob(_data, overwrite=overwrite)
                logger.info(f"Uploaded {storage_key} to Azure Blob Storage.")
            else:
                logger.warning(f"{storage_key} already exists. Skipping upload.")
        
        except Exception as e:
            print(f"Error uploading data to '{container_name}/{storage_key}': {e}")
            raise StorageUploadError(f"Failed to upload file to Azure Blob: {e}")

    

    def download_file(
        self, 
        # storage_unit: str, 
        # storage_path: str, 
        # target_path: str | IO[bytes]
        destination_path: BytesIO | str,
        storage_key: str, 
        container_name: Optional[str], 
    ):
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=storage_key
            )

            data = blob_client.download_blob().readall()

            if hasattr(destination_path, 'write'):
                # If target_path is a file-like object, write data to it
                destination_path.write(data)
                print(f"File '{storage_key}' downloaded from '{container_name}' into memory successfully.")
            else:
                # Otherwise, write data to the specified file path
                dir_path = os.path.dirname(destination_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                with open(destination_path, "wb") as f:
                    f.write(data)
                print(f"File '{storage_key}' downloaded from '{container_name}' to '{destination_path}' successfully.")

        except Exception as e:
            print(f"Error downloading file '{storage_key}' from '{container_name}': {e}")
            raise StorageDownloadError(f"Failed to download file from Azure Blob: {e}")
