from io import BytesIO
import json
import datetime
from storage_lib.utils.logger import logger
from storage_lib.decorators.parquet_decorator import parquet_writes
from storage_lib.utils.latest_stamper import LatestStamper
from typing import Optional

from storage_lib.client_azure import AzureBlobStorageClient
from storage_lib.client_s3 import S3StorageClient

@parquet_writes
class StorageClient:
    azure_storage_constructor = AzureBlobStorageClient
    s3_storage_constructor = S3StorageClient

    """
    Client for Azure Blob Storage / S3 Storage to upload podcast data.
    """
    def __init__(
            self, 
            credentials: dict = None,
            # container_name: str = "whisper",
        ):
        # Azure Blob Storage credentials
        az_storage_account = credentials.get("azure_storage_account", "")
        # S3 credentials
        s3_access_key = credentials.get("s3_access_key", "")
        # stamper placeholder
        self._stamper = None

        # Try Azure Blob Storage client initialization
        if az_storage_account:
            self.storage_client = self.azure_storage_constructor(
                azure_storage_account = credentials.get("azure_storage_account", ""),
                azure_storage_key = credentials.get("azure_storage_key", "")
            )
            # self.storage_client.container_name = container_name

        # Try S3 client initialization
        elif s3_access_key:
            self.storage_client = self.s3_storage_constructor(
                s3_access_key = credentials.get("s3_access_key", ""),
                s3_secret_key = credentials.get("s3_secret_key", ""),
                s3_endpoint_url = credentials.get("s3_endpoint_url", ""),
                s3_use_ssl = credentials.get("s3_use_ssl", "true"),
                s3_region_name = credentials.get("s3_region_name", "")
            )
            # self.storage_client.container_name = container_name
        else:
            raise ValueError(
                "No valid storage credentials provided. "
                "Please provide either Azure Blob Storage or S3 credentials."
            )

    def list_containers(self) -> list:
        """
        List all containers in Storage.
        """
        return self.storage_client.list_containers()
    

    def key_exists(
            self, 
            container_name: str,
            storage_key: str, 
        ) -> bool:
        """
        Check if a file exists in Storage.
        """
        return self.storage_client.key_exists(
            container_name=container_name,
            storage_key=storage_key
        )



    def upload_object(
            self, 
            storage_key: str, 
            source: BytesIO,
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Upload a file to Storage.
        """
        self.storage_client.upload_object(
            storage_key=storage_key,
            source=source,
            container_name=container_name,
            overwrite=overwrite
        )


    def set_latest_stamper(
            self, 
            utc_time: Optional[datetime.datetime] = None
        ) -> LatestStamper:
        """
        Set the latest timestamp stamper.
        """
        self._stamper = LatestStamper(
            utc_time=utc_time or datetime.datetime.now(datetime.UTC)
        )

    @property
    def stamper(self) -> LatestStamper:
        """
        Get the latest timestamp stamper.
        """
        if not self._stamper:
            self.set_latest_stamper()
        return self._stamper

    def upload_file(
            self, 
            storage_key: str, 
            source: str,
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Upload a file to Storage.
        """
        self.storage_client.upload_file(
            storage_key=storage_key,
            source=source,
            container_name=container_name,
            overwrite=overwrite
        )


    def upload_timestamp(
            self, 
            storage_key: str, 
            container_name: str, 
            utc_time: Optional[datetime.datetime] = None,
            overwrite: bool = True
        ) -> None:
        """
        Upload a timestamp to Storage.
        """
        self.set_latest_stamper(utc_time=utc_time)

        logger.info(f"Uploading latest timestamp to {container_name}/{storage_key}")

        self.storage_client.upload_object(
            storage_key=storage_key,
            source=self._stamper.json_bytes_io,
            container_name=container_name,
            overwrite=overwrite
        )

    
    def download_object(
            self, 
            storage_key: str,
            container_name: str,
        ) -> BytesIO:
        """
        Download a file from Storage and return it as a BytesIO object.
        """
        return self.storage_client.download_object(
            container_name=container_name, 
            storage_key=storage_key,
        )


    def download_json(
            self, 
            storage_key: str,
            container_name: str,
        ) -> dict:
        """
        Download a JSON file from Azure Blob Storage and return it as a dictionary.
        """
        bytesIO = self.storage_client.download_object(
            container_name=container_name, 
            storage_key=storage_key,
        )
        print("Download successful, reading JSON file...")

        # Read the JSON file from BytesIO object
        json_data = bytesIO.read().decode('utf-8')
        return json.loads(json_data)
    


    def upload_json(
            self, 
            storage_key: str, 
            data: dict | list,
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Upload a JSON file to Storage.
        This method converts the provided data (dict or list) to a JSON string,
        encodes it to bytes, and uploads it to the specified storage key in the given container.
        """
        json_data = json.dumps(data, indent=4)
        source = BytesIO(json_data.encode('utf-8'))
        self.upload_object(
            storage_key=storage_key,
            source=source,
            container_name=container_name,
            overwrite=overwrite
        )