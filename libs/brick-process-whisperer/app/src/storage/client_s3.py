import os
import boto3
from app.src.logging_config import logger
from app.src.storage.errors import StorageDownloadError, StorageUploadError
from typing import IO, Optional
from io import BytesIO
from app.src.utils import Validate


class S3StorageClient:
    def __init__(
        self, 
        s3_access_key: str,
        s3_secret_key: str,
        s3_endpoint_url: str,
        s3_use_ssl: str,
        s3_region_name: str
        
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



    # def storage_unit_exists(self, bucket_name: str) -> bool:
    #     try:
    #         response = self.s3_client.list_buckets()
    #         for bucket in response['Buckets']:
    #             if bucket['Name'] == bucket_name:
    #                 return True
    #         return False
    #     except Exception as e:
    #         print(f"Error checking existence of bucket '{bucket_name}': {e}")
    #         return False
        


    # def create_storage_unit(self, bucket_name: str):
    #     try:
    #         if not self.storage_unit_exists(bucket_name):
    #             self.s3_client.create_bucket(Bucket=bucket_name)
    #             print(f"Bucket '{bucket_name}' created successfully.")
    #         else:
    #             print(f"Bucket '{bucket_name}' already exists.")
    #     except Exception as e:
    #         print(f"Error creating bucket '{bucket_name}': {e}")
    #         raise Exception(f"Failed to create bucket '{bucket_name}': {e}")



    # def list_storage_units(self):
    #     try:
    #         response = self.s3_client.list_buckets()
    #         print("S3 Buckets:")
    #         for bucket in response['Buckets']:
    #             print(f"  - {bucket['Name']}")
    #     except Exception as e:
    #         print(f"Error listing S3 buckets: {e}")


    # object_key = storage_path
    # bucket_name = storage_unit

    # def upload_file(
    #     self, 
    #     source_path: str, 
    #     storage_unit: str, 
    #     storage_path: str
    # ):
    # def upload_file(
    #         self, 
    #         source: BytesIO | str,
    #         storage_key: str, 
    #         container_name: Optional[str], 
    #         overwrite: bool = True
    #     ) -> None:
    #     try:
    #         self.s3_client.upload_file(
    #             source, 
    #             container_name, 
    #             storage_key
    #         )
    #         print(f"File '{source}' uploaded to bucket '{container_name}' as '{storage_key}'.")
    #     except Exception as e:
    #         print(f"Error uploading file '{source}' to bucket '{container_name}': {e}")
    #         raise StorageUploadError(f"Failed to upload file to S3: {e}")


    def upload_file(
            self, 
            storage_key: str, 
            source: BytesIO | str,
            container_name: Optional[str], 
            overwrite: bool = True
        ) -> None:
        """
        Upload a file to S3 Storage.
        """

        Validate.non_empty_string(storage_key, "storage_key")
        # Validate.is_instance(source, BytesIO, "source")

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
            container_name = container_name or self._container_name
            
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
                Fileobj=_data,
                Bucket=container_name, 
                Key=storage_key
            )

            logger.info(
                f"File {storage_key} uploaded to {container_name} successfully."
            )

        except Exception as e:
            print(f"Error uploading data to '{container_name}/{storage_key}': {e}")
            raise StorageUploadError(f"Failed to upload file to S3: {e}")

    

    # def download_file(
    #     self, 
    #     storage_unit: str, 
    #     storage_path: str, 
    #     target_path: str | IO[bytes]
    # ):
    def download_file(
        self, 
        destination_path: BytesIO | str,
        storage_key: str, 
        container_name: Optional[str], 
    ):
        try:
            if hasattr(destination_path, "write"):
                # Download to memory buffer
                response = self.s3_client.get_object(
                    Bucket=container_name, 
                    Key=storage_key
                )
                destination_path.write(response["Body"].read())
                print(
                    f"File '{storage_key}' downloaded from "
                    f"bucket '{container_name}' into memory successfully."
                )
            else:
                # Download to local file path
                dir_path = os.path.dirname(destination_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                self.s3_client.download_file(
                    container_name, 
                    storage_key, 
                    destination_path
                )
                print(
                    f"File '{storage_key}' downloaded from "
                    f"bucket '{container_name}' to '{destination_path}'."
                )

        except Exception as e:
            print(f"Error downloading file '{storage_key}' from bucket '{container_name}': {e}")
            raise StorageDownloadError(f"Failed to download file from S3: {e}")            
        
