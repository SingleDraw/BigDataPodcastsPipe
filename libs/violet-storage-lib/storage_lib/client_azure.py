import os
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from storage_lib.errors import StorageUploadError, StorageDownloadError
from storage_lib.utils.logger import logger
from typing import Optional
from storage_lib.utils.validate import Validate


class AzureBlobStorageClient:
    """
    Client for Azure Blob Storage to upload podcast data.
    """
    def __init__(
            self, 
            azure_storage_account: Optional[str],
            azure_storage_key: Optional[str] = None,
            azure_storage_connection_string: Optional[str] = None
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

            if not credential:
                raise ValueError("DefaultAzureCredential could not be initialized.")

            # try:
            #     # Get a token for the Azure Storage service
            #     # This is necessary to ensure the credential is valid and raises an error if not
            #     # Otherwise it wont exit the program if the credential is invalid
            #     _ = credential.get_token("https://storage.azure.com/.default")
            # except Exception as e:
            #     raise ValueError(f"Failed to get Azure token: {e}")

            self.blob_service_client = BlobServiceClient(
                account_url=f"https://{azure_storage_account}.blob.core.windows.net",
                credential=credential
            )
        else:
            raise ValueError(
                "Azure Storage Account and Key must be provided for string based authentication."
                "Or at least Azure Storage Account for DefaultAzureCredential."
            )

    def list_containers(
            self
        ) -> list:
        """
        List all containers in the Azure Blob Storage account.
        """
        try:
            containers = self.blob_service_client.list_containers()
            return [container.name for container in containers]
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            raise StorageDownloadError(f"Failed to list containers: {e}")


    def key_exists(
            self, 
            container_name: str,
            storage_key: str, 
        ) -> bool:
        """
        Check if a blob exists in Azure Blob Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name or self.container_name, 
            blob=storage_key
        )
        
        return blob_client.exists()


    def upload_file(
            self, 
            source: str,
            storage_key: str, 
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Upload a blob to Azure Blob Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")
        Validate.is_instance(source, str, "source")

        if not os.path.exists(source):
            raise FileNotFoundError(f"Local file {source} does not exist.")
        
        with open(source, "rb") as f:
            _data = BytesIO(f.read())
    
        self.upload_object(
            source=_data, 
            storage_key=storage_key, 
            container_name=container_name, 
            overwrite=overwrite
        )
        


    def upload_object(
            self, 
            source: BytesIO,
            storage_key: str, 
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Upload a BytesIO object to Azure Blob Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")
        Validate.is_instance(source, BytesIO, "source")

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=storage_key
            )

            if not blob_client.exists() or overwrite:
                source.seek(0)  # Reset pointer for proper read
                blob_client.upload_blob(source, overwrite=overwrite)
                logger.info(f"Uploaded {storage_key} to Azure Blob Storage.")
            else:
                logger.warning(f"{storage_key} already exists. Skipping upload.")
        
        except Exception as e:
            print(f"Error uploading data to '{container_name}/{storage_key}': {e}")
            raise StorageUploadError(f"Failed to upload file to Azure Blob: {e}")


    def _get_existing_blob_client(self, container_name: str, blob_name: str):
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        if not blob_client.exists():
            raise FileNotFoundError(f"Blob {blob_name} does not exist in container {container_name}.")
        return blob_client


    def download_object(
            self, 
            storage_key: str, 
            container_name: str, 
        ) -> BytesIO:
        """
        Download a blob from Azure Blob Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")

        blob_client = self._get_existing_blob_client(
            container_name=container_name, 
            blob_name=storage_key
        )

        try:
            download_stream = blob_client.download_blob()
            data = BytesIO(download_stream.readall())
            data.seek(0)  # Reset pointer for proper read
            logger.info(f"Downloaded {storage_key} from Azure Blob Storage.")
            return data 
        
        except Exception as e:
            raise StorageDownloadError(
                f"Failed to download file from Azure Blob: {e}"
            )
        


    def download_file(
            self, 
            storage_key: str, 
            container_name: str, 
            destination_path: str
        ) -> None:
        """
        Download a blob from Azure Blob Storage to a local file.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")
        Validate.non_empty_string(destination_path, "destination_path")

        blob_client = self._get_existing_blob_client(
            container_name=container_name, 
            blob_name=storage_key
        )

        try:
            download_stream = blob_client.download_blob()

        except Exception as e:
            raise StorageDownloadError(
                f"Failed to download file from Azure Blob: {e}"
            )
    
        # Write the data to the destination file
        destination_dir = os.path.dirname(destination_path)

        try:
            if destination_dir and not os.path.exists(destination_dir):
                os.makedirs(destination_dir)

            with open(destination_path, "wb") as f:
                f.write(download_stream.readall())
            
            logger.info(f"Downloaded {storage_key} to {destination_path}.")
        except Exception as e:
            raise StorageDownloadError(
                f"Failed to write downloaded file to {destination_path}: {e}"
            )