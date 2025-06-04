import os
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from app.src.logging_config import logger
from app.src.storage.parquet_decorator import parquet_writes
from typing import Optional

@parquet_writes
class AzureBlobStorageClient:
    """
    Client for Azure Blob Storage to upload podcast data.
    """
    def __init__(
            self, 
            azure_storage_account: str = os.getenv("AZURE_STORAGE_ACCOUNT", ""),
            azure_storage_key: str = os.getenv("AZURE_STORAGE_KEY", ""),
            container_name: str = "whisper"
        ):
        if azure_storage_account and azure_storage_key:
            """
            Use connection string for authentication.
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
                token = credential.get_token("https://storage.azure.com/.default")
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


        self._container_name = container_name



    @property
    def container_name(self) -> str:
        return self._container_name
    
    @container_name.setter
    def container_name(self, value: str) -> None:
        self._container_name = value



    def get_container_client(
            self, 
            container_name: str
        ) -> BlobServiceClient:
        return self.blob_service_client.get_container_client(
            container_name
        )


    def create_container(
            self, 
            container_name: str
        ) -> None:
        """
        Create a container in Azure Blob Storage.
        """
        container_client = self.get_container_client(
            container_name
        )
        
        if container_client.exists():
            logger.warning(f"Container '{container_name}' already exists.")
            return
        try:
            container_client.create_container()
            logger.info(f"Container '{container_name}' created successfully.")
        except Exception as e:
            logger.error(f"Failed to create container '{container_name}': {e}")


    def blob_exists(
            self, 
            container_name: str,
            blob_path: str, 
        ) -> bool:
        """
        Check if a blob exists in Azure Blob Storage.
        """
        container_client = self.get_container_client(
            self.container_name if not container_name else container_name
        )
        
        blob_client = container_client.get_blob_client(blob_path)
        return blob_client.exists()


    def upload_blob(
            self, 
            blob_path: str, 
            data: BytesIO,
            container_name: Optional[str], 
            overwrite: bool = True
        ) -> None:
        """
        Upload a blob to Azure Blob Storage.
        """
        container_client = self.get_container_client(
            self.container_name if not container_name else container_name
        )

        blob_client = container_client.get_blob_client(blob_path)

        if not blob_client.exists() or overwrite:
            data.seek(0)  # Reset pointer for proper read
            blob_client.upload_blob(data, overwrite=overwrite)
            logger.info(f"Uploaded {blob_path} to Azure Blob Storage.")
        else:
            logger.warning(f"{blob_path} already exists. Skipping upload.")
