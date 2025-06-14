import os
from io import BytesIO
import boto3
from storage_lib.utils.logger import logger
from typing import Optional
from storage_lib.errors import StorageUploadError, StorageDownloadError
from storage_lib.utils.validate import Validate

class S3StorageClient:
    """
    Client for S3 Storage to upload podcast data.
    This client uses Boto3 to interact with S3 Storage.
    """
    def __init__(
            self, 
            s3_access_key: str,
            s3_secret_key: str,
            s3_endpoint_url: str = "",
            s3_use_ssl: str = "true",
            s3_region_name: str = ""
        ):

        Validate.non_empty_string(s3_access_key, "s3_access_key")

        if not s3_access_key or not s3_secret_key:
            raise ValueError(
                "S3 Access Key and Secret Key must be provided for authentication."
            )
        
        # Normalize s3_use_ssl to a boolean value
        if isinstance(s3_use_ssl, str):
            s3_use_ssl_val = s3_use_ssl.lower() in ('true', '1', 'yes')
        else:
            s3_use_ssl_val = s3_use_ssl

        # Prepare the kwargs for boto3 client initialization
        kwargs = {}
        for key, value in [
            ('aws_access_key_id', s3_access_key),
            ('aws_secret_access_key', s3_secret_key),
            ('endpoint_url', s3_endpoint_url), 
            ('use_ssl', s3_use_ssl_val), 
            ('region_name', s3_region_name)
        ]:
            if value not in (None, ''):
                kwargs[key] = value

        self.s3_client = boto3.client('s3', **kwargs)


    def key_exists(
            self, 
            container_name: str,
            storage_key: str, 
        ) -> bool:
        """
        Check if a file exists in S3 Storage.
        """

        Validate.non_empty_string(container_name, "container_name")
        Validate.non_empty_string(storage_key, "storage_key")

        try:
            self.s3_client.head_object(
                Bucket=container_name, 
                Key=storage_key
            )
            return True
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise  # Re-raise if it's a different error

    def list_containers(
            self
        ) -> list:
        """
        List all containers (buckets) in S3 Storage.
        """
        try:
            buckets_dict=self.s3_client.list_buckets().get('Buckets', [])
            return [bucket['Name'] for bucket in buckets_dict]
        except Exception as e:
            raise StorageDownloadError(
                f"Failed to list containers in S3: {e}"
            )


    def upload_file(
            self, 
            storage_key: str, 
            source: str,
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Upload a file to S3 Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")
        Validate.is_instance(source, str, "source")

        if not os.path.exists(source):
            raise FileNotFoundError(f"Local file {source} does not exist.")
        
        # Read the file into a BytesIO object
        with open(source, "rb") as f:
            _data = BytesIO(f.read())
        _data.seek(0)

        self.upload_object(
            storage_key=storage_key, 
            source=_data, 
            container_name=container_name, 
            overwrite=overwrite
        )



    def upload_object(
            self, 
            storage_key: str, 
            source: BytesIO,
            container_name: str, 
            overwrite: bool = True
        ) -> None:
        """
        Upload a file to S3 Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")
        Validate.is_instance(source, BytesIO, "source")

        try:
            # Check for existing file if overwrite is False
            if not overwrite:
                try:
                    self.s3_client.head_object(
                        Bucket=container_name, 
                        Key=storage_key
                    )
                    logger.warning(f"{storage_key} already exists. Skipping upload.")
                    return 
                except self.s3_client.exceptions.ClientError as e:
                    # If the error is 404, the file does not exist
                    # If it's a different error, re-raise it
                    if e.response['Error']['Code'] != '404':
                        raise

            # Upload from BytesIO
            self.s3_client.upload_fileobj(
                Fileobj=source,
                Bucket=container_name, 
                Key=storage_key
            )

            logger.info(
                f"File {storage_key} uploaded to {container_name} successfully."
            )

        except Exception as e:
            raise StorageUploadError(
                f"Failed to upload file to S3: {e}"
            )


    def download_object(
            self, 
            storage_key: str, 
            container_name: str
        ) -> BytesIO:
        """
        Download a file from S3 Storage.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")

        try:
            response = self.s3_client.get_object(
                Bucket=container_name, 
                Key=storage_key
            )
            data = BytesIO(response['Body'].read())
            data.seek(0)
            logger.info(f"File {storage_key} downloaded from {container_name} successfully.")
            return data
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"File {storage_key} not found in {container_name}.")
            raise StorageDownloadError(
                f"Failed to download file from S3: {e.response['Error']['Message']}"
            )
        
    def download_file(
            self, 
            storage_key: str, 
            container_name: str, 
            destination_path: str,
            overwrite: bool = True
        ) -> None:
        """
        Download a file from S3 Storage to a local path.
        """
        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")
        Validate.non_empty_string(destination_path, "destination_path")

        try:
            if not overwrite and os.path.exists(destination_path):
                logger.warning(f"File already exists at {destination_path}. Skipping download.")
                return
            
            dir_path = os.path.dirname(destination_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            self.s3_client.download_file(
                Bucket=container_name, 
                Key=storage_key, 
                Filename=destination_path
            )
            logger.info(
                f"File {storage_key} downloaded from {container_name} to {destination_path} successfully."
            )
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"File {storage_key} not found in {container_name}.")
            raise StorageDownloadError(
                f"Failed to download file from S3: {e.response['Error']['Message']}"
            )