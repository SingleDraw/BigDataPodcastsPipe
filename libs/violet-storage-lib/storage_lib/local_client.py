


import os
from io import BytesIO
from storage_lib.decorators.parquet_decorator import parquet_writes
from storage_lib.utils.validate import Validate


@parquet_writes
class LocalStorageClient:
    """
    A class to handle local storage for debugging purposes.
    It provides methods to save and retrieve data 
    in a local tmp directory as if it were in Azure Blob Storage.
    """

    def __init__(
            self,
            *args,
            **kwargs
        ):
        """
        Initialize the LocalStorageClient.
        This client is used for debugging purposes and does not connect to any remote storage.
        """
        pass


    def key_exists(
            self, 
            storage_key: str, 
            container_name: str = "debug"
        ) -> bool:
        """
        Check if a file exists in the local storage.
        :param file_path: The path of the file to check.
        :param container_name: The name of the container (not used in local storage).
        :return: True if the file exists, False otherwise.
        """
        Validate.non_empty_string(storage_key, "file_path")
        Validate.non_empty_string(container_name, "container_name")

        full_blob_path = f"tmp/{container_name}/{storage_key}"
        return os.path.exists(full_blob_path)
    

    def upload_object(
            self, 
            storage_key: str, 
            source: BytesIO, 
            container_name: str = "debug",
            overwrite: bool = True
        ) -> None:
        """
        Save data to a local file for debugging.
        :param blob_path: The path where the data will be saved.
        :param data: The data to save.
        :param container_name: The name of the container (not used in local storage).
        :param overwrite: Whether to overwrite the file if it exists.
        """

        Validate.non_empty_string(storage_key, "storage_key")
        Validate.non_empty_string(container_name, "container_name")
        Validate.is_instance(source, BytesIO, "source")

        mode = 'wb' if overwrite else 'ab'
        # Ensure the directory exists
        full_blob_path = f"tmp/{container_name}/{storage_key}"
        os.makedirs(
            os.path.dirname(f"tmp/{container_name}/{storage_key}"),
            exist_ok=True
        )

        with open(full_blob_path, mode) as f:
            f.write(source.getvalue()) # gets the bytes from BytesIO


client = LocalStorageClient()